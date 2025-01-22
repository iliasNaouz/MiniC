#! /usr/bin/env python3
import pytest
import glob
import os
import sys
from test_expect_pragma import TestExpectPragmas, cat, TestCompiler, filter_pathnames

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE == os.path.realpath('.'):
    HERE = '.'
TEST_DIR = HERE
IMPLEM_DIR = HERE

SKIP_EXPECT = False
if 'SKIP_EXPECT' in os.environ:
    SKIP_EXPECT = True

DISABLE_TYPECHECK = False  # True to skip typechecking

ALL_FILES = []
# tests for typing AND evaluation
ALL_FILES += glob.glob(os.path.join(TEST_DIR, 'TP03/tests/provided/**/*.c'), recursive=True)
ALL_FILES += glob.glob(os.path.join(TEST_DIR, 'TP03/tests/students/**/*.c'), recursive=True)


# Path setting
if 'TEST_FILES' in os.environ:
    ALL_FILES = glob.glob(os.environ['TEST_FILES'], recursive=True)
MINIC_EVAL = os.path.join(IMPLEM_DIR, 'MiniCC.py')

if 'FILTER' in os.environ:
    ALL_FILES = filter_pathnames(ALL_FILES, os.environ['FILTER'])


class TestInterpret(TestExpectPragmas, TestCompiler):
    DISABLE_CODEGEN = False

    def evaluate(self, file):
        if not DISABLE_TYPECHECK:
            res = self.run_command([sys.executable, MINIC_EVAL, "--mode", "eval", file])
        else:
            res = self.run_command([sys.executable, MINIC_EVAL, "--mode", "eval",
                                   "--disable-typecheck", file])
        if res.exitcode == 1:
            # Execution can't distinguish exit code at runtime and static rejection
            # of the program. But we know that an exit code of 1 is reserved for
            # runtime errors, hence convert this exitcode into an execcode.
            res = res._replace(exitcode=0, execcode=1)
        return res

    # Not in test_expect_pragma to get assertion rewritting
    def assert_equal(self, actual, expected, compiler):
        if expected.output is not None and actual.output is not None:
            assert actual.output == expected.output, \
                f"Output of the program is incorrect (using {compiler})."
        assert actual.exitcode == expected.exitcode, \
            f"Exit code of the compiler ({compiler}) is incorrect"
        assert actual.execcode == expected.execcode, \
            f"Exit code of the execution is incorrect (using {compiler})"

    @pytest.mark.parametrize('filename', ALL_FILES)
    def test_expect(self, filename):
        """Test the EXPECTED annotations in test files by launching the
        program with GCC."""
        if SKIP_EXPECT:
            pytest.skip("Skipping all test_expect because $SKIP_EXPECT is set.")
        expect = self.get_expect(filename)
        if expect.skip_test_expected:
            pytest.skip("Skipping test_expect with GCC because "
                        "the test contains SKIP TEST EXPECTED")
        if expect.exitcode != 0:
            # GCC is more permissive than us, so trying to compile an
            # incorrect program would bring us no information (it may
            # compile, or fail with a different message...)
            pytest.skip("Not testing the expected value for tests expecting exitcode!=0")
        gcc_result = self.run_with_gcc(filename, expect)
        self.assert_equal(gcc_result, expect, "gcc")

    @pytest.mark.parametrize('filename', ALL_FILES)
    def test_eval(self, filename):
        cat(filename)  # For diagnosis
        expect = self.get_expect(filename)
        actual = self.evaluate(filename)
        if expect:
            self.assert_equal(actual, expect, "MiniCC")


if __name__ == '__main__':
    pytest.main(sys.argv)

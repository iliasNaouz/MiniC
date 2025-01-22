#! /usr/bin/env python3

import os
import sys
import pytest
import glob
from test_expect_pragma import (
    TestExpectPragmas, TestCompiler, env_str_variable,
    filter_pathnames
    )

"""
Usage:
    python3 test_codegen.py
(or make test)
"""

"""
MIF08 and CAP, 2019
Unit test infrastructure for testing code generation:
1) compare the actual output to the expected one (in comments)
2) compare the actual output to the one obtained by simulation
3) for different allocation algorithms
"""

MINICC_OPTS = []
if "MINICC_OPTS" in os.environ and os.environ["MINICC_OPTS"]:
    MINICC_OPTS = os.environ["MINICC_OPTS"].split()
else:
    MINICC_OPTS = ["--mode=codegen-cfg"]

DISABLE_TYPECHECK = "--disable-typecheck" in MINICC_OPTS \
    or "--mode=parse" in MINICC_OPTS or "parse" in MINICC_OPTS
DISABLE_CODEGEN = "--mode=parse" in MINICC_OPTS or "--mode=typecheck" in MINICC_OPTS \
    or "parse" in MINICC_OPTS or "typecheck" in MINICC_OPTS

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE == os.path.realpath('.'):
    HERE = '.'
TEST_DIR = HERE
IMPLEM_DIR = HERE
SKIP_EXPECT = False
if 'SKIP_EXPECT' in os.environ:
    SKIP_EXPECT = True

MINIC_COMPILE = os.path.join(IMPLEM_DIR, 'MiniCC.py')

ALL_FILES = []
# tests for typing AND evaluation
ALL_FILES += glob.glob(os.path.join(TEST_DIR, 'TP04/tests/provided/**/[a-zA-Z]*.c'),
                       recursive=True)
ALL_FILES += glob.glob(os.path.join(TEST_DIR, 'TP04/tests/students/**/[a-zA-Z]*.c'),
                       recursive=True)


ALLOC_FILES = glob.glob(os.path.join(HERE, 'TP05/tests/**/*.c'), recursive=True)

SKIP_NOT_IMPLEMENTED = False
if 'SKIP_NOT_IMPLEMENTED' in os.environ:
    SKIP_NOT_IMPLEMENTED = True

if 'TEST_FILES' in os.environ:
    ALL_FILES = glob.glob(os.environ['TEST_FILES'], recursive=True)

MINIC_EVAL = os.path.join(
HERE, '..', '..', 'TP03', 'MiniC-type-interpret', 'Main.py')

# if 'COMPIL_MINIC_EVAL' in os.environ:
#     MINIC_EVAL = os.environ['COMPIL_MINIC_EVAL']
# else:
#     MINIC_EVAL = os.path.join(
#         HERE, '..', '..', 'TP03', 'MiniC-type-interpret', 'Main.py')

# Avoid duplicates
ALL_IN_MEM_FILES = list(set(ALL_FILES) | set(ALLOC_FILES))
ALL_IN_MEM_FILES.sort()
ALL_FILES = list(set(ALL_FILES))
ALL_FILES.sort()

if 'TEST_FILES' in os.environ:
    ALLOC_FILES = ALL_FILES
    ALL_IN_MEM_FILES = ALL_FILES

if 'FILTER' in os.environ:
    ALL_FILES = filter_pathnames(ALL_FILES, os.environ['FILTER'])
    ALLOC_FILES = filter_pathnames(ALLOC_FILES, os.environ['FILTER'])
    ALL_IN_MEM_FILES = filter_pathnames(ALL_IN_MEM_FILES, os.environ['FILTER'])


class TestCodeGen(TestExpectPragmas, TestCompiler):
    DISABLE_CODEGEN = DISABLE_CODEGEN
    SKIP_NOT_IMPLEMENTED = SKIP_NOT_IMPLEMENTED
    MINIC_COMPILE = MINIC_COMPILE
    MINICC_OPTS = MINICC_OPTS

    # Not in test_expect_pragma to get assertion rewritting
    def assert_equal(self, actual, expected, compiler):
        if DISABLE_CODEGEN and expected.exitcode in (0, 5):
            # Compiler does not fail => no output expected
            assert actual.output == "", \
                "Compiler unexpectedly generated some output with codegen disabled"
            assert actual.exitcode == 0, \
                "Compiler unexpectedly failed with codegen disabled"
            return
        if DISABLE_TYPECHECK and expected.exitcode != 0:
            # Test should fail at typecheck, and we don't do
            # typechecking => nothing to check.
            pytest.skip("Test that doesn't typecheck with --disable-typecheck")
        assert actual.exitcode == expected.exitcode, \
            f"Exit code of the compiler ({compiler}) is incorrect"
        if expected.output is not None and actual.output is not None:
            assert actual.output == expected.output, \
                f"Output of the program is incorrect (using {compiler})."
        assert actual.execcode == expected.execcode, \
            f"Exit code of the execution is incorrect (after compiling with {compiler})"

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
        self.assert_equal(gcc_result, expect, "GCC")

    @pytest.mark.parametrize('filename', ALL_FILES)
    def test_naive_alloc(self, filename):
        expect = self.get_expect(filename)
        naive = self.compile_and_simulate(filename, expect, 'naive')
        self.assert_equal(naive, expect, "MiniCC with naive alloc")

    @pytest.mark.parametrize('filename', ALL_IN_MEM_FILES)
    def test_alloc_mem(self, filename):
        expect = self.get_expect(filename)
        actual = self.compile_and_simulate(filename, expect, 'all-in-mem')
        self.assert_equal(actual, expect, "MiniCC with all-in-mem")

    @pytest.mark.parametrize('filename', ALL_IN_MEM_FILES)
    def test_alloc_hybrid(self, filename):
        expect = self.get_expect(filename)
        actual = self.compile_and_simulate(filename, expect, 'hybrid')
        self.assert_equal(actual, expect, "MiniCC with hybride naive alloc")

    @pytest.mark.parametrize('filename', ALL_IN_MEM_FILES)
    def test_smart_alloc(self, filename):
        """Generate code with smart allocation."""
        expect = self.get_expect(filename)
        actual = self.compile_and_simulate(filename, expect, 'smart')
        self.assert_equal(actual, expect, "MiniCC with smart alloc")


if __name__ == '__main__':
    pytest.main(sys.argv)

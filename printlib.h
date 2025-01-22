#include <stdio.h>
/**
 * Compatibility layer with C (meant to be #included in MiniC source
 * files). Defines types, constants and functions that are built-in
 * MiniC, to allow compiling MiniC programs with GCC.
 */

typedef char * string;
typedef int bool;
static const int true = 1;
static const int false = 0;

void print_int(int);
void println_int(int);
void println_bool(int);

#define print_float(f) do { printf("%.2f", f); } while(0)
#define println_float(f) do { printf("%.2f\n", f); } while(0)

void print_string(string);
void println_string(string);

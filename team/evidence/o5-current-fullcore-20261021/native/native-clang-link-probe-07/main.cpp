#include "VProbe.h"
#include <iostream>
int main() { VProbe p; p.a=41; p.eval(); std::cout << p.b << "\n"; return p.b == 42 ? 0 : 1; }

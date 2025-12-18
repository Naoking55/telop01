#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from analyze_prtextstyle_structure import analyze_file

print("Analyzing TEMPLATE files...")
binary1, rgba1 = analyze_file("TEMPLATE_SolidFill_White.prtextstyle")
print("\n" + "="*80)
binary2, rgba2 = analyze_file("TEMPLATE_SolidFill_White_StrokeBlack.prtextstyle")

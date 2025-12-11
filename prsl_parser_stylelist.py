#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRSL Parser for 'stylelist' format
This parser handles the XML-based PRSL format with <stylelist><styleblock> structure
"""

import sys
from typing import List, Tuple
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field

# Import data classes from modern converter
sys.path.insert(0, '/home/user/telop01')
try:
    from prsl_converter_modern import Style, Fill, Stroke, Shadow, GradientStop
except ImportError:
    # Define data classes if import fails
    @dataclass
    class GradientStop:
        position: float = 0.0
        midpoint: float = 0.5
        r: int = 255
        g: int = 255
        b: int = 255
        a: int = 255

    @dataclass
    class Fill:
        fill_type: str = "solid"
        r: int = 255
        g: int = 255
        b: int = 255
        a: int = 255
        gradient_stops: List[GradientStop] = field(default_factory=list)
        gradient_angle: float = 0.0

    @dataclass
    class Stroke:
        width: float = 1.0
        r: int = 0
        g: int = 0
        b: int = 0
        a: int = 255

    @dataclass
    class Shadow:
        enabled: bool = False
        offset_x: float = 2.0
        offset_y: float = 2.0
        blur: float = 4.0
        r: int = 0
        g: int = 0
        b: int = 0
        a: int = 120

    @dataclass
    class Style:
        name: str = "Unnamed Style"
        font_family: str = "Arial"
        font_size: float = 64.0
        fill: Fill = field(default_factory=Fill)
        strokes: List[Stroke] = field(default_factory=list)
        shadow: Shadow = field(default_factory=Shadow)


class StylelistPRSLParser:
    """Parser for stylelist-based PRSL format"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.styles: List[Style] = []

    def parse(self) -> List[Style]:
        """Parse PRSL file and return list of Styles"""
        try:
            tree = ET.parse(self.filepath)
            root = tree.getroot()

            if root.tag != 'stylelist':
                print(f"⚠ Warning: Expected <stylelist> root, got <{root.tag}>")
                return []

            # Parse each styleblock
            for styleblock in root.findall('styleblock'):
                style = self._parse_styleblock(styleblock)
                if style:
                    self.styles.append(style)

            print(f"✓ Parsed {len(self.styles)} styles from {self.filepath}")
            return self.styles

        except Exception as e:
            print(f"✗ Error parsing {self.filepath}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_styleblock(self, styleblock: ET.Element) -> Style:
        """Parse a single styleblock element"""
        # Get style name
        name = styleblock.attrib.get('name', 'Unnamed Style')

        # Create Style object
        style = Style(name=name)

        # Parse text_specification (font info)
        text_spec = styleblock.find('text_specification')
        if text_spec is not None:
            self._parse_text_specification(text_spec, style)

        # Parse style_data (fill, stroke, shadow)
        style_data = styleblock.find('style_data')
        if style_data is not None:
            self._parse_style_data(style_data, style)

        return style

    def _parse_text_specification(self, text_spec: ET.Element, style: Style):
        """Parse text_specification (font information)"""
        font = text_spec.find('font')
        if font is not None:
            # Font family
            family = font.find('family')
            if family is not None and family.text:
                style.font_family = family.text.strip()

            # Font size
            size = font.find('size')
            if size is not None and size.text:
                try:
                    style.font_size = float(size.text)
                except ValueError:
                    pass

    def _parse_style_data(self, style_data: ET.Element, style: Style):
        """Parse style_data (fill, stroke, shadow)"""
        # Parse fill (face > shader > colouring)
        face = style_data.find('face')
        if face is not None:
            shader = face.find('shader')
            if shader is not None:
                colouring = shader.find('colouring')
                if colouring is not None:
                    self._parse_colouring(colouring, style)

        # Parse shadow
        shadow_elem = style_data.find('shadow')
        if shadow_elem is not None:
            self._parse_shadow(shadow_elem, style)

        # Parse strokes (embellishment__0, embellishment__1, etc.)
        # Note: This format uses "embellishment" for strokes
        # For now, we'll skip detailed stroke parsing

    def _parse_colouring(self, colouring: ET.Element, style: Style):
        """Parse colouring (fill color/gradient)"""
        # Check type: 5=solid, others=gradient
        type_elem = colouring.find('type')
        if type_elem is not None and type_elem.text:
            colour_type = int(type_elem.text)
        else:
            colour_type = 5  # default to solid

        if colour_type == 5:
            # Solid color
            solid = colouring.find('solid_colour')
            if solid is not None:
                all_elem = solid.find('all')
                if all_elem is not None:
                    r, g, b, a = self._parse_rgba(all_elem)
                    style.fill = Fill(
                        fill_type="solid",
                        r=r, g=g, b=b, a=a
                    )
        else:
            # Gradient (two_colour_ramp, four_colour_ramp, etc.)
            two_colour = colouring.find('two_colour_ramp')
            if two_colour is not None:
                self._parse_two_colour_gradient(two_colour, style)

    def _parse_rgba(self, elem: ET.Element) -> Tuple[int, int, int, int]:
        """Parse RGBA from element (values are 0.0-1.0 floats)"""
        def get_color_component(name: str) -> int:
            comp = elem.find(name)
            if comp is not None and comp.text:
                try:
                    # Convert 0.0-1.0 to 0-255
                    return int(float(comp.text) * 255)
                except ValueError:
                    pass
            return 255 if name == 'alpha' else 0

        r = get_color_component('red')
        g = get_color_component('green')
        b = get_color_component('blue')
        a = get_color_component('alpha')

        return (r, g, b, a)

    def _parse_two_colour_gradient(self, two_colour: ET.Element, style: Style):
        """Parse two-color gradient"""
        stops = []

        # Top color (position 0.0)
        top = two_colour.find('top')
        if top is not None:
            r, g, b, a = self._parse_rgba(top)
            stops.append(GradientStop(position=0.0, r=r, g=g, b=b, a=a))

        # Bottom color (position 1.0)
        bottom = two_colour.find('bottom')
        if bottom is not None:
            r, g, b, a = self._parse_rgba(bottom)
            stops.append(GradientStop(position=1.0, r=r, g=g, b=b, a=a))

        # Angle
        angle_elem = two_colour.find('angle')
        angle = 0.0
        if angle_elem is not None and angle_elem.text:
            try:
                angle = float(angle_elem.text)
            except ValueError:
                pass

        if stops:
            style.fill = Fill(
                fill_type="gradient",
                gradient_stops=stops,
                gradient_angle=angle
            )

    def _parse_shadow(self, shadow_elem: ET.Element, style: Style):
        """Parse shadow element"""
        # Check if shadow is enabled
        on_elem = shadow_elem.find('on')
        if on_elem is not None and on_elem.text:
            enabled = on_elem.text.strip().lower() == 'true'
        else:
            enabled = False

        if not enabled:
            return

        # Blur (softness)
        softness = shadow_elem.find('softness')
        blur = 4.0
        if softness is not None and softness.text:
            try:
                blur = float(softness.text) / 10.0  # Scale to reasonable value
            except ValueError:
                pass

        # Color
        colour = shadow_elem.find('colour')
        r, g, b, a = (0, 0, 0, 120)
        if colour is not None:
            r, g, b, a = self._parse_rgba(colour)

        # Offset (angle + magnitude)
        offset = shadow_elem.find('offset')
        offset_x, offset_y = 2.0, 2.0
        if offset is not None:
            angle_elem = offset.find('angle')
            mag_elem = offset.find('magnitude')

            angle = 90.0
            magnitude = 5.0

            if angle_elem is not None and angle_elem.text:
                try:
                    angle = float(angle_elem.text)
                except ValueError:
                    pass

            if mag_elem is not None and mag_elem.text:
                try:
                    magnitude = float(mag_elem.text)
                except ValueError:
                    pass

            # Convert angle+magnitude to x,y offsets
            import math
            rad = math.radians(angle)
            offset_x = magnitude * math.cos(rad)
            offset_y = -magnitude * math.sin(rad)

        style.shadow = Shadow(
            enabled=True,
            offset_x=offset_x,
            offset_y=offset_y,
            blur=blur,
            r=r, g=g, b=b, a=a
        )


def parse_prsl_stylelist(filepath: str) -> List[Style]:
    """Parse stylelist-format PRSL file"""
    parser = StylelistPRSLParser(filepath)
    return parser.parse()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prsl_parser_stylelist.py <prsl_file>")
        sys.exit(1)

    styles = parse_prsl_stylelist(sys.argv[1])
    print(f"\n✓ Total styles parsed: {len(styles)}")

    for i, style in enumerate(styles[:5], 1):
        print(f"\n{i}. {style.name}")
        print(f"   Font: {style.font_family} ({style.font_size}pt)")
        print(f"   Fill: {style.fill.fill_type}")
        if style.fill.fill_type == "solid":
            print(f"   Fill Color: RGB({style.fill.r}, {style.fill.g}, {style.fill.b})")
        else:
            print(f"   Gradient: {len(style.fill.gradient_stops)} stops")
        print(f"   Shadow: {'ON' if style.shadow.enabled else 'OFF'}")

    if len(styles) > 5:
        print(f"\n... and {len(styles) - 5} more styles")

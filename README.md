# Novum - rev2

The split keyboard for me (it may not be for you).

![Novum keyboard](/docs/images/novum.jpg)

## Background

I began my split keyboard journey with the [Lily58](https://github.com/kata0510/Lily58),
and I've been enjoying it. However, the offset of specific columns wasn't optimal
for my hands, and I couldn't comfortably reach certain keys in the thumb fan.
The [Sofle](https://josefadamcik.github.io/SofleKeyboard/) solved some of these
issues, but I decided to create my own split keyboard designed specifically for
my hands.

As part of using the Lily58, I found out:

- I didn't use the "extra" key next to G and H.
- The top left and right keys are too far away to reach.
- Swapping Ctrl and Shift keys in the default layout didn't work for me.

The following split keyboards inspire Novum:

- [Lily58](https://github.com/kata0510/Lily58)
- [Sofle](https://github.com/josefadamcik/SofleKeyboard)
- [Fortitude60](https://github.com/Pekaso/fortitude60)
- [pteron](https://github.com/FSund/pteron-keyboard)

### Design Principles

- Columns located perfectly for my fingers.
- Keep it simple and stupid:
  - No RGB nonsense
  - No display
  - No wireless
- The thumb fan is curved perfectly for my thumb, and the keys are not located under
  the hand.
- Built with [Ergogen](https://github.com/ergogen/ergogen), inspired by
  [corney-island](https://github.com/ceoloide/corney-island/tree/main) and
  [spleeb](https://github.com/chrishoage/spleeb/tree/main).
- Individual PCBs for the left and right sides. My OCD does not like the
  reversible PCBs.

## Generate PCBs

You can find the pre-generated files on the [Releases](https://github.com/Henkru/novum/releases)
page. However, if you want, you can generate the files yourself by executing the
`build.sh` script (requires [Docker](https://www.docker.com)).

The build process consists of multiple phases:

1. Generate the unrouted PCBs.
2. Inject the JLCPCB [design rules](https://github.com/labtroll/KiCad-DesignRules).
3. Import hand-routed tracks into PCBs.
4. [Autoroute](https://freerouting.org) the unconnected items.
5. Use [KiBot](https://github.com/INTI-CMNB/KiBot) to generate gerbers and images.

Each step is located in the `builder/steps` folder. Hand-routed tracks
can be extracted from the `.kicad_pcb` files by executing `npm run export-tracks`.

## Different PCBs

The revision 1 is a typical sandwich design, with each layer intended to be a
1.6 mm thick FR-4 circuit board. This approach reduces costs and streamlines
manufacturing, as it allows all boards to be ordered from a single supplier.

The current design offers three variants for the bottom board. The _standard_
version features intricate PCB art on exposed copper layers and requires an
[ENIG](https://jlcpcb.com/blog/203-choosing-the-right-surface-finish-for-your-pcb/?from=BWBS)
(Electroless Nickel Immersion Gold) surface finish. If this design feels too
elaborate, a blank bottom board is also included in the release package as an
alternative. Additionally, the package contains a bottom board compatible with
splitkb's [tenting puck](https://splitkb.com/products/tenting-puck) accessary,
providing further customization options.

| Top side                                                 | Bottom side                                                 |
| -------------------------------------------------------- | ----------------------------------------------------------- |
| ![](/docs/images/left-top.png)                           | ![](/docs/images/left-bottom.png)                           |
| ![](/docs/images/right-top.png)                          | ![](/docs/images/right-bottom.png)                          |
| ![](/docs/images/switch_plate-top.png)                   | ![](/docs/images/switch_plate-bottom.png)                   |
| ![](/docs/images/bottom_board_with_art-top.png)          | ![](/docs/images/bottom_board_with_art-bottom.png)          |
| ![](/docs/images/bottom_board_empty-top.png)             | ![](/docs/images/bottom_board_empty-bottom.png)             |
| ![](/docs/images/bottom_board_with_tenting_puck-top.png) | ![](/docs/images/bottom_board_with_tenting_puck-bottom.png) |

## BOM

| Item                                                                                                                                     | Quantity | Notes                                                                                                  |
| ---------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------ |
| Novum Left PCB                                                                                                                           | 1        |                                                                                                        |
| Novum Right PCB                                                                                                                          | 1        |                                                                                                        |
| Novum Switch Plate                                                                                                                       | 2        |                                                                                                        |
| Novum Bottom Plate                                                                                                                       | 2        | Three different version available, see [images](https://github.com/Henkru/novum/tree/main/docs/images) |
| [1N4148W Diode](https://www.lcsc.com/product-detail/Switching-Diodes_Jiangsu-Changjing-Electronics-Technology-Co-Ltd-1N4148W_C2099.html) | 60       | SOD-123 or through hole                                                                                |
| [Kailh Hot-Swap Socket](https://www.lcsc.com/product-detail/Mechanical-Keyboard-Shaft_Kailh-CPG151101S11-16_C5156480.html)               | 58       |                                                                                                        |
| [RP2040 Community Edition](https://github.com/qmk/qmk_firmware/blob/master/docs/platformdev_rp2040.md) MCU Board                         | 2        |                                                                                                        |
| [PJ-320A TRRS Jack](https://www.lcsc.com/product-detail/Audio-Connectors-Headphones_XKB-Connection-PJ-320A_C2884926.html)                | 2        |                                                                                                        |
| [SKHLLCA010 Button](https://www.lcsc.com/product-detail/Tactile-Switches_ALPSALPINE-SKHLLCA010_C139766.html)                             | 2        |                                                                                                        |
| [EC11 Encoder](https://www.lcsc.com/product-detail/Rotary-Encoders_ALPSALPINE-EC11E183440C_C370986.html)                                 | 2        |                                                                                                        |
| M2 x 4 mm screw                                                                                                                          | 24       |                                                                                                        |
| M2 x 8 mm spacer                                                                                                                         | 12       | Outer diameter: 3.1 mm                                                                                 |

## Firmware

Any [RP2040 Community Edition](https://github.com/qmk/qmk_firmware/blob/master/docs/platformdev_rp2040.md)
standard boards should. However, the keyboard is only tested with [Liatris](https://splitkb.com/products/liatris)
and [SparkFun Pro Micro - RP2040](https://www.sparkfun.com/products/18288) boards.
The following firmware is currently supported, and the pre-build binaries can
be found on the [Releases](https://github.com/Henkru/novum/releases) page.

- [QMK](https://github.com/qmk/qmk_firmware)
- [Vial](https://github.com/vial-kb/vial-qmk)

Currently, the keyboard has yet to be merged into the above mainline repos.

## Default Layout

![The default layout for the keyboard](/docs/layout/rev2_vial.svg)

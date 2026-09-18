# Cinematic hype promo — spec edit

An original 14-second vertical spec edit demonstrating cinematic pacing, warm/teal color treatment, motion typography, transitions, sound design, and a polished social export.

- [Watch or download the MP4](cinematic-hype-spec.mp4)
- [View the six-frame preview](cinematic-hype-preview.jpg)
- [Inspect the build script](build_cinematic_spec.py)

This is transparent spec work, not a prior client project. The edit, typography system, timing, color treatment, and original synthesized audio bed are by Youssef Bayoumy. The source footage consists of free Mixkit stock previews used under the Mixkit Video Free License.

Source clip IDs: 26100, 4949, 49939, 51373, and 12132.

- Mixkit video license: https://mixkit.co/license/#videoFree
- Mixkit free stock video catalogue: https://mixkit.co/free-stock-video/

The source preview files are not bundled in this repository. The script documents the editing pipeline and can rebuild the piece when the five cited Mixkit previews are placed in the workspace `outputs` directory. Build locally with Python 3.10, MoviePy, Pillow, and NumPy:

```powershell
python build_cinematic_spec.py
```

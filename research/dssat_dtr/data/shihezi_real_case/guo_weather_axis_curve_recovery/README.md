# Guo Fig.2-2 numeric-axis and colored-curve recovery

One numeric-only OCR pass was used only to identify axis digits. Curve points are obtained from the original embedded JPEG by HSV color segmentation and continuity filtering.

- image size: 3460 x 1072
- numeric OCR tokens retained: 25

## 2019 panel
- refined plot rect: `[312, 1535, 152, 842]`
- nearby numeric OCR: `[{'text': '50', 'conf': 96.741806, 'left': 236, 'top': 96, 'width': 64, 'height': 47}, {'text': '15', 'conf': 96.480194, 'left': 1551, 'top': 96, 'width': 56, 'height': 47}, {'text': '40', 'conf': 94.527466, 'left': 234, 'top': 240, 'width': 66, 'height': 46}, {'text': '12', 'conf': 96.780029, 'left': 1551, 'top': 239, 'width': 58, 'height': 46}, {'text': '30', 'conf': 96.751091, 'left': 236, 'top': 384, 'width': 64, 'height': 46}, {'text': '720', 'conf': 0.0, 'left': 145, 'top': 527, 'width': 155, 'height': 80}, {'text': '10', 'conf': 95.638878, 'left': 241, 'top': 671, 'width': 59, 'height': 47}, {'text': '0301', 'conf': 69.045525, 'left': 246, 'top': 815, 'width': 128, 'height': 90}, {'text': '0521', 'conf': 95.908554, 'left': 446, 'top': 859, 'width': 128, 'height': 46}, {'text': '0610063007200809', 'conf': 0.0, 'left': 646, 'top': 859, 'width': 732, 'height': 46}, {'text': '0828', 'conf': 87.165268, 'left': 1445, 'top': 813, 'width': 132, 'height': 92}, {'text': '4', 'conf': 0.0, 'left': 836, 'top': 955, 'width': 135, 'height': 71}]`

## 2020 panel
- refined plot rect: `[2053, 3276, 136, 839]`
- nearby numeric OCR: `[{'text': '15', 'conf': 95.248032, 'left': 3293, 'top': 93, 'width': 56, 'height': 47}, {'text': '50', 'conf': 0.0, 'left': 1882, 'top': 93, 'width': 159, 'height': 63}, {'text': '7', 'conf': 0.0, 'left': 2922, 'top': 108, 'width': 265, 'height': 49}, {'text': '40', 'conf': 96.881088, 'left': 1975, 'top': 237, 'width': 66, 'height': 47}, {'text': '12', 'conf': 95.197647, 'left': 3293, 'top': 236, 'width': 58, 'height': 46}, {'text': '30', 'conf': 96.794815, 'left': 1977, 'top': 381, 'width': 64, 'height': 46}, {'text': '20', 'conf': 96.94828, 'left': 1976, 'top': 524, 'width': 65, 'height': 47}, {'text': '6', 'conf': 0.0, 'left': 3287, 'top': 515, 'width': 135, 'height': 55}, {'text': '10', 'conf': 96.587219, 'left': 1983, 'top': 668, 'width': 58, 'height': 47}, {'text': '0301', 'conf': 68.263313, 'left': 1988, 'top': 812, 'width': 128, 'height': 90}, {'text': '0521', 'conf': 96.138657, 'left': 2188, 'top': 856, 'width': 128, 'height': 46}, {'text': '0610063007200809', 'conf': 0.0, 'left': 2388, 'top': 856, 'width': 732, 'height': 46}, {'text': '0828', 'conf': 80.580872, 'left': 3186, 'top': 810, 'width': 132, 'height': 92}]`

## Curve pixel summaries

|Year|Color|Points|Horizontal coverage %|Y min|Y max|Bottom-connected tall cols|
|---:|---|---:|---:|---:|---:|---:|
|2019|red|1200|98.0|244.0|630.0|0|
|2019|cyan|411|33.6|618.0|838.0|464|
|2020|red|1193|97.5|253.5|561.0|0|
|2020|cyan|131|10.7|138.0|834.5|471|

Interpretation rule: a temperature curve should have high horizontal coverage and low bottom-connected tall-column count; a rainfall fill/legend will show bottom connectivity or fragmented coverage.

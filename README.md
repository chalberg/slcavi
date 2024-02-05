# slcavi

Exploration of avalanches in the Wasatch mountains using historical avalanche and climate data.

---
## Table of Contents

- [About](#about)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Contributing](#contributing)
- [Liscense](#liscense)

---
## About <a name="about"></a>

This project is focused on providing information about avalanches in the Wasatch range. The main feature of this respository is an interactive map displaying avalanche incidents and additional information about the event.

![Avalanche Map (screenshot)](static/assets/maps/avi_map.png)

---
## Getting Started <a name="getting-started"></a>

Download this repository using the following commands:
```bash
$ git clone https://github.com/chalberg/slcavi.git
$ cd slcavi
$ pip install -r requirements.txt
```
---
## Usage <a name="usage"></a>

**Launching the App**
The main feature of this repository is a web app which displays an interactive map of avalanche incidents in the Wasatch mountains. To launch the app, ensure you have all the requirements installed and run the following commands:
```bash
$ cd slcavi
$ python app.py
```
This will launch the app and generate some text, including the following link:
```
* Running on http://127.0.0.1:5000
```
Paste this link into your brower to access the app.

**Generating the Map**
To generate the interactive map pictured above, navigate to this directory and run the following command:
```bash
$ python visualizations.py --save
```
---
## Contributing <a name="contributing"></a>


---
## Liscense <a name="liscense"></a>

MIT License

Copyright (c) [2024] [Charlie Halberg]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
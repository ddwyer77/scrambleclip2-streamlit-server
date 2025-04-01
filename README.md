# ScrambleClip2 by ClipModeGo

ScrambleClip2 is a powerful video remixing tool that creates unique scrambled videos from your clips.

## Features

- Upload multiple videos to combine into seamlessly scrambled remixes
- Add custom audio tracks to enhance your videos
- Add text overlays with customizable font size, color, and stroke
- Generate multiple unique videos at once
- Easy download options for single videos or all generated videos
- Clean, modern UI that's easy to use

## How to Use

1. **Upload Videos**: Upload one or more video files (MP4, MOV, etc.)
2. **Add Audio** (Optional): Upload an audio file to be used in the generated videos
3. **Configure Settings**:
   - Number of output videos to generate
   - Segment duration (how long each clip should be)
   - Text overlay options (optional)
4. **Generate Videos**: Click the "Generate Scrambled Videos" button
5. **Download**: Download individual videos or all videos as a ZIP

## Text Overlay Options

- **Enable Text Overlay**: Check the box to add text to your videos
- **Text Content**: Enter the text you want to display
- **Text Color**: Choose the color for your text
- **Stroke Color**: Choose the color for the text outline
- **Font Size**: Adjust the size of the text (20-100)
- **Stroke Width**: Adjust the thickness of the outline (0-10)
- **Text Opacity**: Adjust the transparency of the text (0.0-1.0)

## Requirements

- Python 3.8+
- Streamlit
- MoviePy
- OpenCV
- NumPy

## Deployment

This app is deployed on Streamlit Cloud and can be accessed at:
[https://ddwyer77-scrambleclip2-streamlit-server.streamlit.app/](https://ddwyer77-scrambleclip2-streamlit-server.streamlit.app/)

## Local Development

To run this app locally:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## License

© 2024 ClipModeGo. All rights reserved. 
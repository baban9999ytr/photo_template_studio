# Privacy & Local Processing Guarantee

## 100% Offline Local Processing

We prioritize your privacy and data security. All core photo processing tasks, including image scaling, framing, drawing, annotations, and AI image upscaling, happen **entirely offline** on your local hardware.

- No images, templates, or project metadata are ever uploaded to the cloud or sent to remote servers.
- We do not collect telemetry, usage metrics, or any tracking data.
- If you use **Ollama** for text polishing, all LLM inference occurs securely and privately on your local CPU/GPU.

## Paid Cloud API Privacy

When you choose to utilize paid cloud models (e.g., OpenAI ChatGPT, Google Gemini) via the Text Studio:

- Text payloads (your rough input text and our system prompt) are transmitted securely and directly between your local machine and the official API endpoints of the respective providers.
- These requests are authenticated using your personal API keys, which are stored securely and locally on your machine in the `.env` file. We never have access to your API keys.
- We recommend reviewing the respective privacy policies of OpenAI and Google regarding data retention for API calls.

## Disclaimers & Liability

- **AI Output Disclaimer:** AI-generated text output is provided "as is" without any guarantees regarding factual accuracy, tone appropriateness, or trademark/copyright compliance. Please review all AI-generated content before publishing.
- **Third-Party Trademark Disclaimer:** Photo Template Studio Pro (PictureFormatter) is an independent, open-source project. It is not affiliated with, endorsed by, or partnered with OpenAI, Google, Ollama, Meta, Instagram, or Real-ESRGAN.
- **Limitation of Liability:** The software is provided "AS IS". The developer assumes no liability for any data loss, workflow disruption, or hardware stress/damage that may occur during intensive high-resolution photo processing or VRAM scaling tasks.

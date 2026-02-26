from pydantic import BaseModel, Field


class WhatsAppSendMessageRequest(BaseModel):
    numbers: list[str] = Field(
        ...,
        description=(
            "Recipient phones list. Use international digits format without '+' (e.g., 201090253864). "
            "Local 01... format is also accepted and normalized to 201..."
        ),
        examples=[["201xxxxxxxxx", "010xxxxxxxx", "+201xxxxxxxxx"]],
    )
    message: str = Field(
        ...,
        description="Text message to send.",
        examples=["Hello from PhysioAssist bot"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "numbers": ["201090253864", "01140011394"],
                "message": """مرحبًا 👋
خلينا نفهم المشكلة سوا قبل ما تيجي العيادة.

من خلال شوية أسئلة بسيطة، هنقدر نكوّن صورة أوضح عن حالتك،
وكمان هتساعدك تعرف الفرق بين الألم الطبيعي اللي بيعدّي،
والألم اللي محتاج تدخل منظم.

⏱️ الوقت المتوقع: دقيقتين تقريبًا.
⚠️ ده مش تشخيص طبي، لكنه خطوة أولى للفهم الصحيح.

يلا نبدأ؟""",
            }
        }


class WhatsAppSendMessageItemResult(BaseModel):
    to: str
    chat_id: str
    message: str
    status: str
    error: str | None = None


class WhatsAppSendMessageResponse(BaseModel):
    status: str
    requested_count: int
    sent_count: int
    failed_count: int
    results: list[WhatsAppSendMessageItemResult]

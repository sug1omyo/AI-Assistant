"""
Thinking Generator - Generates live reasoning/thinking steps for AI responses.

Provides real-time thinking display similar to ChatGPT's "thinking" feature.
Analyzes the user's message and generates DYNAMIC, SPECIFIC thinking steps
that reflect actual analysis of the message content.
"""
import re
import logging
from typing import Generator, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Special prefix for reasoning content from models (Grok, DeepSeek R1, etc.)
REASONING_PREFIX = '\x02REASON\x03'


@dataclass
class ThinkingStep:
    """A single thinking step"""
    text: str
    duration_ms: int = 300
    category: str = 'general'


# ─── Message Analysis ─────────────────────────────────────────────

def _extract_keywords(message: str) -> List[str]:
    """Extract meaningful keywords/phrases from the message"""
    # Remove common stop words (Vietnamese + English)
    stop_words = {
        'là', 'và', 'của', 'cho', 'với', 'trong', 'được', 'có', 'không',
        'này', 'đó', 'một', 'các', 'những', 'để', 'từ', 'lại', 'đã',
        'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 'or', 'but',
        'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that',
        'it', 'i', 'you', 'he', 'she', 'we', 'they', 'my', 'your',
        'can', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
        'tôi', 'bạn', 'mình', 'cậu', 'anh', 'chị', 'em', 'nó', 'họ',
        'hãy', 'xin', 'vui', 'lòng', 'giúp', 'ơi', 'nhé', 'nha', 'ạ',
    }
    # Split and filter
    words = re.findall(r'[\w]+', message.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 1]
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:8]  # Limit


def _detect_intent(message: str) -> Tuple[str, str]:
    """
    Detect the intent/category and a short intent description.
    Returns (category, intent_description)
    """
    msg = message.lower().strip()

    patterns = [
        ('greeting', r'(xin chào|chào|hello|hi |hey|good morning|good evening)',
         'Chào hỏi / bắt đầu cuộc trò chuyện'),
        ('code', r'(code|function|class|bug|error|debug|implement|refactor|api|'
         r'algorithm|database|sql|html|css|javascript|python|java|deploy|docker|git|'
         r'lập trình|hàm|lỗi|sửa|viết code|triển khai|syntax|compile|runtime)',
         'Yêu cầu liên quan đến lập trình'),
        ('explain', r'(explain|giải thích|tại sao|why|how does|làm sao|như thế nào|cách)',
         'Yêu cầu giải thích / hướng dẫn'),
        ('analysis', r'(analyze|analysis|compare|evaluate|phân tích|so sánh|đánh giá)',
         'Yêu cầu phân tích / đánh giá'),
        ('creative', r'(write|story|poem|create|design|imagine|compose|draft|'
         r'viết|truyện|thơ|tạo|thiết kế|sáng tạo|soạn|bài viết)',
         'Yêu cầu sáng tạo nội dung'),
        ('math', r'(calculate|math|equation|solve|formula|tính|toán|phương trình|giải)',
         'Bài toán / tính toán'),
        ('translate', r'(translate|dịch|translation|bản dịch|chuyển ngữ|sang tiếng)',
         'Yêu cầu dịch thuật'),
        ('summary', r'(summarize|summary|tóm tắt|tổng kết|overview|recap)',
         'Yêu cầu tóm tắt'),
        ('planning', r'(plan|strategy|roadmap|schedule|kế hoạch|chiến lược|lộ trình|quy trình)',
         'Lập kế hoạch / chiến lược'),
        ('research', r'(research|study|paper|science|theory|nghiên cứu|khoa học|lý thuyết)',
         'Nghiên cứu / tìm hiểu'),
        ('opinion', r'(what do you think|ý kiến|nghĩ gì|đánh giá|recommend|gợi ý|nên)',
         'Hỏi ý kiến / gợi ý'),
    ]

    for category, pattern, desc in patterns:
        if re.search(pattern, msg):
            return category, desc

    # Detect question
    if re.search(r'[?？]|\b(what|where|when|who|which|gì|đâu|bao giờ|ai|nào)\b', msg):
        return 'question', 'Câu hỏi cần phản hồi'

    if len(msg) > 100:
        return 'complex', 'Yêu cầu phức tạp, nhiều nội dung'

    return 'general', 'Xử lý tin nhắn'


def _truncate(text: str, max_len: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + '...'


# ─── Thinking Step Generation ─────────────────────────────────────

def generate_thinking_steps(
    message: str,
    language: str = 'vi',
    context: str = 'casual',
    deep_thinking: bool = False,
) -> Generator[ThinkingStep, None, None]:
    """
    Generate DYNAMIC thinking steps that analyze the actual message.
    Each step shows real reasoning about the user's input.
    """
    vi = language == 'vi'
    category, intent_desc = _detect_intent(message)
    keywords = _extract_keywords(message)
    msg_short = _truncate(message, 60)
    kw_str = ', '.join(keywords[:4]) if keywords else msg_short

    # ── Step 1: Understand the input ──
    if vi:
        yield ThinkingStep(
            text=f'🔍 Đọc và phân tích: "{msg_short}"',
            duration_ms=250, category=category,
        )
    else:
        yield ThinkingStep(
            text=f'🔍 Reading and analyzing: "{msg_short}"',
            duration_ms=250, category=category,
        )

    # ── Step 2: Identify intent ──
    if vi:
        yield ThinkingStep(
            text=f'🎯 Xác định ý định: {intent_desc}',
            duration_ms=200, category=category,
        )
    else:
        yield ThinkingStep(
            text=f'🎯 Identified intent: {intent_desc}',
            duration_ms=200, category=category,
        )

    # ── Step 3: Category-specific analysis ──
    if category == 'greeting':
        if vi:
            yield ThinkingStep(
                text='💬 Người dùng chào hỏi → chuẩn bị phản hồi thân thiện, tự nhiên',
                duration_ms=200, category=category,
            )
        else:
            yield ThinkingStep(
                text='💬 User greeting → preparing friendly, natural response',
                duration_ms=200, category=category,
            )

    elif category == 'code':
        if vi:
            yield ThinkingStep(
                text=f'💻 Từ khóa kỹ thuật: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='⚙️ Phân tích yêu cầu → xác định giải pháp kỹ thuật phù hợp',
                duration_ms=300, category=category,
            )
            yield ThinkingStep(
                text='🔧 Xem xét edge cases, best practices và xử lý lỗi',
                duration_ms=250, category=category,
            )
        else:
            yield ThinkingStep(
                text=f'💻 Technical keywords: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='⚙️ Analyzing requirements → identifying appropriate technical solution',
                duration_ms=300, category=category,
            )
            yield ThinkingStep(
                text='🔧 Considering edge cases, best practices and error handling',
                duration_ms=250, category=category,
            )

    elif category == 'explain':
        if vi:
            yield ThinkingStep(
                text=f'📖 Chủ đề cần giải thích: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='🧠 Xây dựng giải thích rõ ràng, dễ hiểu với ví dụ minh họa',
                duration_ms=300, category=category,
            )
        else:
            yield ThinkingStep(
                text=f'📖 Topic to explain: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='🧠 Building clear explanation with illustrative examples',
                duration_ms=300, category=category,
            )

    elif category == 'analysis':
        if vi:
            yield ThinkingStep(
                text=f'📊 Đối tượng phân tích: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='🔬 Đánh giá đa chiều → liên kết dữ liệu và rút ra kết luận',
                duration_ms=350, category=category,
            )
        else:
            yield ThinkingStep(
                text=f'📊 Analysis subject: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='🔬 Multi-dimensional evaluation → connecting data and drawing conclusions',
                duration_ms=350, category=category,
            )

    elif category == 'creative':
        if vi:
            yield ThinkingStep(
                text=f'🎨 Chủ đề sáng tạo: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='✍️ Phát triển ý tưởng → xây dựng cấu trúc nội dung',
                duration_ms=300, category=category,
            )
        else:
            yield ThinkingStep(
                text=f'🎨 Creative topic: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='✍️ Developing ideas → building content structure',
                duration_ms=300, category=category,
            )

    elif category == 'math':
        if vi:
            yield ThinkingStep(
                text=f'📐 Nhận diện bài toán: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='🔢 Xác định phương pháp → thực hiện tính toán từng bước',
                duration_ms=350, category=category,
            )
        else:
            yield ThinkingStep(
                text=f'📐 Problem identified: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='🔢 Identifying method → performing step-by-step calculation',
                duration_ms=350, category=category,
            )

    elif category == 'translate':
        if vi:
            yield ThinkingStep(
                text='🌐 Phân tích ngữ cảnh và sắc thái ngôn ngữ',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='📝 Chuyển đổi tự nhiên, giữ nguyên ý nghĩa gốc',
                duration_ms=300, category=category,
            )
        else:
            yield ThinkingStep(
                text='🌐 Analyzing context and language nuances',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='📝 Natural conversion, preserving original meaning',
                duration_ms=300, category=category,
            )

    elif category in ('question', 'opinion'):
        if vi:
            yield ThinkingStep(
                text=f'🤔 Nội dung câu hỏi liên quan đến: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='💡 Thu thập thông tin → đưa ra câu trả lời chính xác',
                duration_ms=300, category=category,
            )
        else:
            yield ThinkingStep(
                text=f'🤔 Question relates to: {kw_str}',
                duration_ms=250, category=category,
            )
            yield ThinkingStep(
                text='💡 Gathering information → formulating accurate answer',
                duration_ms=300, category=category,
            )

    else:
        # general / complex
        if keywords:
            if vi:
                yield ThinkingStep(
                    text=f'🧩 Từ khóa chính: {kw_str}',
                    duration_ms=200, category=category,
                )
            else:
                yield ThinkingStep(
                    text=f'🧩 Key topics: {kw_str}',
                    duration_ms=200, category=category,
                )
        if vi:
            yield ThinkingStep(
                text='🧠 Xử lý và suy luận về nội dung yêu cầu',
                duration_ms=250, category=category,
            )
        else:
            yield ThinkingStep(
                text='🧠 Processing and reasoning about the request',
                duration_ms=250, category=category,
            )

    # ── Deep thinking extra steps ──
    if deep_thinking:
        if vi:
            yield ThinkingStep(
                text='🔬 Phân tích sâu: xem xét từ nhiều góc độ khác nhau',
                duration_ms=350, category=category,
            )
            yield ThinkingStep(
                text='⚖️ Cân nhắc ưu nhược điểm và các phương án thay thế',
                duration_ms=300, category=category,
            )
        else:
            yield ThinkingStep(
                text='🔬 Deep analysis: examining from multiple perspectives',
                duration_ms=350, category=category,
            )
            yield ThinkingStep(
                text='⚖️ Weighing pros/cons and alternative approaches',
                duration_ms=300, category=category,
            )

    # ── Final step: composing ──
    context_labels = {
        'casual': 'thoải mái' if vi else 'casual',
        'programming': 'kỹ thuật' if vi else 'technical',
        'creative': 'sáng tạo' if vi else 'creative',
        'research': 'học thuật' if vi else 'academic',
        'psychological': 'tâm lý' if vi else 'psychological',
        'lifestyle': 'đời sống' if vi else 'lifestyle',
    }
    ctx_label = context_labels.get(context, context)
    if vi:
        yield ThinkingStep(
            text=f'📝 Tổng hợp câu trả lời (phong cách: {ctx_label})',
            duration_ms=200, category=category,
        )
    else:
        yield ThinkingStep(
            text=f'📝 Composing response (style: {ctx_label})',
            duration_ms=200, category=category,
        )


def detect_category(message: str) -> str:
    """Detect the category of a message"""
    category, _ = _detect_intent(message)
    return category


def generate_thinking_summary(
    message: str,
    category: str,
    language: str = 'vi',
) -> str:
    """Generate a brief summary of the thinking process"""
    vi = language == 'vi'
    summaries = {
        'greeting': ('Đã phân tích và chuẩn bị phản hồi',
                     'Analyzed and prepared response'),
        'code': ('Đã phân tích yêu cầu lập trình và chuẩn bị giải pháp',
                 'Analyzed programming request and prepared solution'),
        'explain': ('Đã phân tích chủ đề và xây dựng giải thích',
                    'Analyzed topic and built explanation'),
        'analysis': ('Đã phân tích đa chiều và tổng hợp kết luận',
                     'Multi-dimensional analysis and synthesis complete'),
        'creative': ('Đã phát triển ý tưởng và hoàn thiện nội dung',
                     'Developed ideas and refined content'),
        'math': ('Đã giải quyết bài toán qua các bước logic',
                 'Solved problem through logical steps'),
        'translate': ('Đã phân tích ngữ cảnh và chuyển đổi ngôn ngữ',
                      'Analyzed context and performed translation'),
        'summary': ('Đã xác định điểm chính và tóm tắt',
                    'Identified key points and summarized'),
        'planning': ('Đã phân tích yêu cầu và lập kế hoạch',
                     'Analyzed requirements and created plan'),
        'research': ('Đã tổng hợp kiến thức và nghiên cứu',
                     'Synthesized knowledge and research'),
        'question': ('Đã phân tích câu hỏi và chuẩn bị câu trả lời',
                     'Analyzed question and prepared answer'),
        'opinion': ('Đã đánh giá và chuẩn bị gợi ý',
                    'Evaluated and prepared recommendation'),
        'general': ('Đã phân tích và chuẩn bị câu trả lời',
                    'Analyzed and prepared response'),
        'complex': ('Đã phân tích yêu cầu phức tạp và chuẩn bị phản hồi',
                    'Analyzed complex request and prepared response'),
    }
    pair = summaries.get(category, summaries['general'])
    return pair[0] if vi else pair[1]

"""Legacy market field contracts; current grade reports do not import this schema."""

# The whitelist is deliberately explicit.  In particular, no 收款、成交、退费、
# 单效、订单 or other outcome field is allowed to enter the message.
PROCESS_FIELDS: tuple[str, ...] = (
    "期次",
    "顾问",
    "主管",
    "部门",
    "渠道",
    "退前线索",
    "退后线索",
    "线索留存率",
    "总通时",
    "首call完成数",
    "首call率",
    "6h外呼",
    "12h外呼",
    "24h外呼",
    "48h外呼",
    "48h外呼数",
    "外呼频次",
    "外呼次数",
    "5min",
    "5min线索数",
    "好友率",
    "好友线索数",
    "APP登陆率",
    "APP登陆线索数",
    "深沟率",
    "深沟线索数",
    "双沟率",
    "双沟线索数",
)

TEXT_FIELDS: tuple[str, ...] = (
    "说明",
    "推送标题",
    "推送期次",
    "推送说明",
    "计算_提醒顾问",
    "提醒",
)

TEXT_SECTION_ORDER: tuple[str, ...] = ("过程数据", "结果数据")

HELPER_RAW_FIELDS: tuple[str, ...] = ("期次", "顾问", "主管", "渠道")
HELPER_DIMENSION_FIELDS: tuple[str, ...] = ("维度键", "顾问", "主管", "渠道")

# Result data is read from the already-aggregated ``IP播报_主管 / 结果数据``
# view.  Keeping this projection separate from PROCESS_FIELDS is intentional:
# outcome fields must not leak into the process section, while the result
# section is explicitly allowed to show the business result metrics.
RESULT_FIELDS: tuple[str, ...] = (
    "期次",
    "经理",
    "主管",
    "顾问",
    "渠道",
    "退前线索",
    "退后线索",
    "线索留存率",
    "首call率",
    "48h外呼",
    "5min",
    "好友率",
    "深沟率",
    "双沟率",
    "首节到课率",
    "单效（当期）",
    "人均报科",
    "人头转化",
    "订单转化",
    "收款",
    "退费",
    "退费率",
    "净收款",
    "单效",
    "报科数",
    "成交人头",
    "当期净收款",
    "当期报科数",
    "当期成交人头",
)

RESULT_IMAGE_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("期次", "期", "text"),
    ("经理", "经理", "text"),
    ("主管", "主管", "text"),
    ("退前线索", "退前线索", "count"),
    ("退后线索", "退后线索", "count"),
    ("线索留存率", "线索留存率", "rate"),
    ("首call率", "首call率", "rate"),
    ("48h外呼", "48h外呼", "rate"),
    ("5min", "5min", "rate"),
    ("好友率", "好友率", "rate"),
    ("深沟率", "深沟率", "rate"),
    ("双沟率", "双沟率", "rate"),
    ("首节到课率", "首节到课率", "rate"),
    ("单效（当期）", "单效(当期)", "number"),
    ("人均报科", "人均报科", "number"),
    ("人头转化", "人头转化", "rate"),
    ("订单转化", "订单转化", "rate"),
    ("净收款", "净收款", "amount"),
    ("退费率", "退费率", "rate"),
    ("单效", "单效", "number"),
)

RESULT_RATE_DENOMINATORS: dict[str, str] = {
    "线索留存率": "退前线索",
    "首call率": "退后线索",
    "48h外呼": "退后线索",
    "5min": "退后线索",
    "好友率": "退后线索",
    "深沟率": "退后线索",
    "双沟率": "退后线索",
    "首节到课率": "退后线索",
    "人头转化": "退后线索",
    "订单转化": "退后线索",
}

RESULT_SUM_FIELDS: tuple[str, ...] = (
    "退前线索",
    "退后线索",
    "收款",
    "退费",
    "净收款",
    "报科数",
    "成交人头",
    "当期净收款",
    "当期报科数",
    "当期成交人头",
)

RESULT_BAR_FIELDS: dict[str, str] = {
    "首call率": "#4f78ae",
    "5min": "#62bc7f",
    "双沟率": "#138de2",
    "人均报科": "#f5ae23",
    "退费率": "#fb5a68",
}

RESULT_IMAGE_WIDTHS: dict[str, int] = {
    "渠道": 400,
    "期次": 140,
    "经理": 180,
    "主管": 180,
    "退前线索": 155,
    "退后线索": 155,
    "线索留存率": 190,
    "首call率": 150,
    "48h外呼": 150,
    "5min": 150,
    "好友率": 150,
    "深沟率": 150,
    "双沟率": 150,
    "首节到课率": 170,
    "单效（当期）": 185,
    "人均报科": 180,
    "人头转化": 165,
    "订单转化": 165,
    "净收款": 175,
    "退费率": 150,
    "单效": 155,
}

IMAGE_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("期次", "期次", "text"),
    ("顾问", "负责人", "text"),
    ("主管", "主管", "text"),
    ("退前线索", "退前线索", "count"),
    ("退后线索", "退后线索", "count"),
    ("线索留存率", "线索留存率", "rate"),
    ("总通时", "总通时", "duration"),
    ("首call率", "首call", "rate"),
    ("6h外呼", "6h外呼", "rate"),
    ("12h外呼", "12h外呼", "rate"),
    ("24h外呼", "24h外呼", "rate"),
    ("48h外呼", "48h外呼", "rate"),
    ("外呼频次", "外呼频次", "frequency"),
    ("5min", "5min比例", "rate"),
    ("好友率", "好友率", "rate"),
    ("APP登陆率", "APP登录率", "rate"),
    ("深沟率", "深沟率", "rate"),
    ("双沟率", "双沟率", "rate"),
)

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "顾问": ("顾问", "负责人"),
    "APP登陆率": ("APP登陆率", "APP登录率"),
    "APP登陆线索数": ("APP登陆线索数", "APP登录线索数"),
    "5min": ("5min", "5min比例"),
}

RATE_NUMERATORS: dict[str, tuple[str, str]] = {
    "线索留存率": ("退后线索", "退前线索"),
    "首call率": ("首call完成数", "退后线索"),
    "48h外呼": ("48h外呼数", "退后线索"),
    "5min": ("5min线索数", "退后线索"),
    "好友率": ("好友线索数", "退后线索"),
    "APP登陆率": ("APP登陆线索数", "退后线索"),
    "深沟率": ("深沟线索数", "退后线索"),
    "双沟率": ("双沟线索数", "退后线索"),
}

RATE_FIELDS = {source for source, _label, kind in IMAGE_COLUMNS if kind == "rate"}
BAR_FIELDS = {
    "首call率": "#4f78ae",
    "5min": "#f5ae23",
    "双沟率": "#138de2",
}

IMAGE_WIDTHS = {
    "渠道": 400,
    "经理": 175,
    "期次": 155,
    "顾问": 175,
    "主管": 155,
    "退前线索": 155,
    "退后线索": 155,
    "线索留存率": 200,
    "总通时": 155,
    "首call率": 160,
    "6h外呼": 155,
    "12h外呼": 155,
    "24h外呼": 155,
    "48h外呼": 155,
    "外呼频次": 140,
    "5min": 175,
    "好友率": 170,
    "APP登陆率": 195,
    "深沟率": 165,
    "双沟率": 165,
}

OUTCOME_TERMS = ("收款", "成交", "退费", "单效", "订单", "支付", "营收", "收入", "GMV")
IMAGE_ROW_FILTER = "hide_both_lead_counts_zero"

import streamlit as st
import streamlit.components.v1 as components
import math

st.set_page_config(page_title="Scientific Calculator", page_icon="🧮", layout="centered")

st.session_state.setdefault("expression", "")
st.session_state.setdefault("result", None)
st.session_state.setdefault("calculation_error", None)
st.session_state.setdefault("expression_reset", 0)

def safe_tan(degrees):
    """tan(90), tan(270), ... are undefined — raise instead of returning a huge float."""
    normalized = math.fmod(float(degrees), 180.0)
    if normalized < 0:
        normalized += 180.0
    if abs(normalized - 90.0) < 1e-9:
        raise ValueError("undefined")
    return math.tan(math.radians(degrees))


# Must exist before any calculate callback runs
allowed_names = {
    name: obj for name, obj in math.__dict__.items() if not name.startswith("__")
}
allowed_names.update({
    "pi": math.pi,
    "e": math.e,
    "sqrt": math.sqrt,
    "sin": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)),
    "tan": safe_tan,
    "asin": lambda x: math.degrees(math.asin(x)),
    "acos": lambda x: math.degrees(math.acos(x)),
    "atan": lambda x: math.degrees(math.atan(x)),
})

st.html(
    """
    <style>
      .calc-hero {
        text-align: center;
        padding: 1.25rem 1rem 1.5rem;
        margin: 0 0 0.5rem;
        border-radius: 18px;
        background:
          radial-gradient(120% 80% at 50% 0%, rgba(14, 165, 233, 0.18), transparent 55%),
          linear-gradient(180deg, #0f172a 0%, #111827 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        box-shadow: 0 12px 40px rgba(15, 23, 42, 0.35);
      }
      .calc-hero__title {
        margin: 0;
        font-size: clamp(1.55rem, 4vw, 2.15rem);
        font-weight: 750;
        letter-spacing: -0.03em;
        color: #f8fafc;
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      }
      .calc-hero__by {
        display: inline-block;
        margin-top: 0.65rem;
        padding: 0.28rem 0.85rem;
        border-radius: 999px;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        color: #e0f2fe;
        background: rgba(14, 165, 233, 0.18);
        border: 1px solid rgba(56, 189, 248, 0.35);
      }
      .calc-hero__by span {
        color: #38bdf8;
        font-weight: 700;
      }
    </style>
    <div class="calc-hero">
      <h1 class="calc-hero__title">Scientific Calculator</h1>
      <div class="calc-hero__by">by <span>Muhammad Ahsan</span></div>
    </div>
    """
)

def expression_key():
    """Widget key remounts on clear so the text field actually empties."""
    return f"expression_{st.session_state.get('expression_reset', 0)}"


def ensure_expression():
    """Callbacks run before the main body, so initialize here if needed."""
    if "expression" not in st.session_state:
        st.session_state.expression = ""
    key = expression_key()
    if key not in st.session_state:
        st.session_state[key] = st.session_state.expression


def sync_expression(value):
    """Keep canonical expression and the active text_input widget in sync."""
    st.session_state.expression = value
    st.session_state[expression_key()] = value


def reset_result():
    """Clear previous output when the expression is edited (no auto-calculate)."""
    st.session_state.result = None
    st.session_state.calculation_error = None


def non_calculate_button_clicked():
    """True when a keypad/AC/⌫ button caused this rerun (not Enter / = / Calculate)."""
    skip_keys = {"key_equals", "key_calculate"}
    for key, value in st.session_state.items():
        if key.startswith("key_") and key not in skip_keys and value is True:
            return True
    return False


def on_expression_change():
    """Enter commits the field → calculate. Keypad/button focus steals → only reset result."""
    ensure_expression()
    st.session_state.expression = st.session_state[expression_key()]
    if non_calculate_button_clicked():
        reset_result()
        return
    calculate_expression()


def append_to_expression(value):
    ensure_expression()
    sync_expression(st.session_state[expression_key()] + value)
    reset_result()


def clear_expression():
    st.session_state.expression = ""
    st.session_state.expression_reset = st.session_state.get("expression_reset", 0) + 1
    st.session_state[expression_key()] = ""
    reset_result()


def delete_last_character():
    ensure_expression()
    sync_expression(st.session_state[expression_key()][:-1])
    reset_result()


def close_unbalanced_parentheses(expression):
    """Append missing closing parentheses so expressions like sin(2 still evaluate."""
    open_count = expression.count("(")
    close_count = expression.count(")")
    missing = open_count - close_count
    if missing > 0:
        expression += ")" * missing
    return expression


def clean_float(value, digits=12):
    """Remove floating-point noise so cos(90) shows as 0, not 6.12e-17."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        rounded = round(float(value), digits)
        if abs(rounded) < 10 ** (-digits):
            return 0.0
        return rounded
    return value


def calculate_expression():
    ensure_expression()
    expression = st.session_state[expression_key()].strip()
    if not expression:
        sync_expression("")
        st.session_state.result = 0
        st.session_state.calculation_error = None
        return

    expression = close_unbalanced_parentheses(expression)
    sync_expression(expression)

    try:
        st.session_state.result = clean_float(
            eval(
                expression,
                {"__builtins__": None},
                allowed_names,
            )
        )
        st.session_state.calculation_error = None
    except Exception:
        st.session_state.result = None
        st.session_state.calculation_error = "Invalid statement"


def bind_calculator_keyboard():
    """Auto-focus expression input; Escape / Cmd+. triggers All Clear."""
    st.session_state["focus_nonce"] = st.session_state.get("focus_nonce", 0) + 1
    # height must be > 0 or some browsers skip running the script
    components.html(
        f"""
        <script>
        (function () {{
            const win = window.parent;
            const doc = win.document;
            const SELECTOR = 'input[aria-label="Enter Expression"]';
            const nonce = "{st.session_state["focus_nonce"]}";

            function getInput() {{
                return doc.querySelector(SELECTOR);
            }}

            function focusExpression() {{
                const input = getInput();
                if (!input) {{
                    setTimeout(focusExpression, 50);
                    return;
                }}
                input.focus({{ preventScroll: true }});
                const len = input.value.length;
                try {{
                    input.setSelectionRange(len, len);
                }} catch (e) {{}}
            }}

            function isEscape(event) {{
                return (
                    event.key === "Escape" ||
                    event.key === "Esc" ||
                    event.code === "Escape" ||
                    event.keyCode === 27 ||
                    event.which === 27
                );
            }}

            function shouldRedirectKey(event) {{
                if (event.ctrlKey || event.metaKey || event.altKey) return false;
                const active = doc.activeElement;
                if (active && active.matches && active.matches(SELECTOR)) return false;
                if (
                    active &&
                    (active.tagName === "INPUT" ||
                        active.tagName === "TEXTAREA" ||
                        active.isContentEditable)
                ) {{
                    return false;
                }}
                return event.key.length === 1 || event.key === "Backspace" || event.key === "Delete";
            }}

            function triggerAllClear() {{
                if (win.__calcClearing) return;
                win.__calcClearing = true;

                // Clear the visible input immediately (Streamlit may keep stale widget state)
                const input = getInput();
                if (input) {{
                    const setter = Object.getOwnPropertyDescriptor(
                        win.HTMLInputElement.prototype,
                        "value"
                    ).set;
                    setter.call(input, "");
                    input.dispatchEvent(new Event("input", {{ bubbles: true }}));
                    input.dispatchEvent(new Event("change", {{ bubbles: true }}));
                }}

                const clearBtn =
                    doc.querySelector(".st-key-key_clear button") ||
                    Array.from(doc.querySelectorAll("button")).find(
                        (button) => button.textContent.trim() === "AC"
                    );

                if (clearBtn) {{
                    clearBtn.click();
                    win.__calcClearing = false;
                    return;
                }}

                // Fallback if AC button is not in the DOM yet
                const url = new URL(win.location.href);
                url.searchParams.set("ac", "1");
                win.location.href = url.toString();
            }}

            function onKeyDown(event) {{
                // Mac Touch Bar Esc, or Mac shortcut Cmd + .
                const macClearShortcut = event.metaKey && (event.key === "." || event.code === "Period");
                if (isEscape(event) || macClearShortcut) {{
                    event.preventDefault();
                    event.stopPropagation();
                    triggerAllClear();
                    return;
                }}
                if (!shouldRedirectKey(event)) return;
                const input = getInput();
                if (!input) return;
                input.focus({{ preventScroll: true }});
            }}

            if (win.__calcKeydownHandler) {{
                win.removeEventListener("keydown", win.__calcKeydownHandler, true);
                doc.removeEventListener("keydown", win.__calcKeydownHandler, true);
            }}
            win.__calcKeydownHandler = onKeyDown;
            win.addEventListener("keydown", onKeyDown, true);
            doc.addEventListener("keydown", onKeyDown, true);
            win.__calcClearing = false;

            focusExpression();
            console.log("Calculator keyboard bound", nonce);
        }})();
        </script>
        """,
        height=1,
    )


# ESC fallback (?ac=1) — clear before widgets render
if st.query_params.get("ac") == "1":
    clear_expression()
    del st.query_params["ac"]

ensure_expression()
expression = st.text_input(
    "Enter Expression",
    placeholder="e.g., sin(30) + log(10) * sqrt(16)",
    key=expression_key(),
    on_change=on_expression_change,
)
st.session_state.expression = st.session_state[expression_key()]

# Mouse-accessible scientific keypad
keypad_rows = [
    ["sin(", "cos(", "tan(", "sqrt("],
    ["asin(", "acos(", "atan(", "log("],
    ["7", "8", "9", "/"],
    ["4", "5", "6", "*"],
    ["1", "2", "3", "-"],
    ["0", ".", "(", ")"],
    ["pi", "e", "**", "+"],
]

for row_index, row in enumerate(keypad_rows):
    columns = st.columns(4)
    for column_index, label in enumerate(row):
        with columns[column_index]:
            st.button(
                label,
                key=f"key_{row_index}_{column_index}",
                use_container_width=True,
                on_click=append_to_expression,
                args=(label,),
            )

columns = st.columns(4)
with columns[0]:
    st.button("AC", key="key_clear", use_container_width=True, on_click=clear_expression)
with columns[1]:
    st.button("⌫", key="key_delete", use_container_width=True, on_click=delete_last_character)
with columns[2]:
    st.button("%", key="key_modulo", use_container_width=True, on_click=append_to_expression, args=("%",))
with columns[3]:
    st.button("=", key="key_equals", type="primary", use_container_width=True, on_click=calculate_expression)

st.caption("Shortcuts: Enter → Calculate  ·  Esc or ⌘ + . → AC")

st.button(
    "Calculate",
    key="key_calculate",
    type="primary",
    use_container_width=True,
    on_click=calculate_expression,
)

if st.session_state.get("calculation_error"):
    st.error(f"❌ {st.session_state.calculation_error}")
elif st.session_state.get("result") is not None:
    st.success(f"✅ Result: {st.session_state.result}")

bind_calculator_keyboard()

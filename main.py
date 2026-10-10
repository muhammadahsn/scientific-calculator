import streamlit as st
import math

st.set_page_config(page_title="Scientific Calculator", page_icon="🧮", layout="centered")

st.title("Muhammad Ahsan")
st.title("🧮 Scientific Calculator")

def append_to_expression(value):
    st.session_state.expression += value


def clear_expression():
    st.session_state.expression = ""


def delete_last_character():
    st.session_state.expression = st.session_state.expression[:-1]


def calculate_expression():
    try:
        st.session_state.result = eval(
            st.session_state.expression,
            {"__builtins__": None},
            allowed_names,
        )
        st.session_state.calculation_error = None
    except Exception as error:
        st.session_state.result = None
        st.session_state.calculation_error = str(error)


st.session_state.setdefault("expression", "")
expression = st.text_input(
    "Enter Expression",
    placeholder="e.g., sin(30) + log(10) * sqrt(16)",
    key="expression",
    on_change=calculate_expression,
)

# Define allowed functions and constants
allowed_names = {
    name: obj for name, obj in math.__dict__.items() if not name.startswith("__")
}
allowed_names.update({
    "pi": math.pi,
    "e": math.e,
    "sqrt": math.sqrt,
    "sin": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)),
    "tan": lambda x: math.tan(math.radians(x)),
    "asin": lambda x: math.degrees(math.asin(x)),
    "acos": lambda x: math.degrees(math.acos(x)),
    "atan": lambda x: math.degrees(math.atan(x)),
})

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
    st.button("C", key="key_clear", use_container_width=True, on_click=clear_expression)
with columns[1]:
    st.button("⌫", key="key_delete", use_container_width=True, on_click=delete_last_character)
with columns[2]:
    st.button("%", key="key_modulo", use_container_width=True, on_click=append_to_expression, args=("%",))
with columns[3]:
    st.button("=", key="key_equals", type="primary", use_container_width=True, on_click=calculate_expression)

if st.button("Calculate", type="primary", use_container_width=True):
    calculate_expression()

if st.session_state.get("calculation_error"):
    st.error(f"❌ Error: {st.session_state.calculation_error}")
elif st.session_state.get("result") is not None:
    st.success(f"✅ Result: {st.session_state.result}")

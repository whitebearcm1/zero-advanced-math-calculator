import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sympy as sp
import os
import sys


# ==================== 你的原始类，一字未改 ====================
def resource_path(rel):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

class SymbolCalc:
    def __init__(self, formula_str, var_names):
        self.var_names = var_names
        self.syms = sp.symbols(",".join(var_names), seq=True)
        self.sym_dict = {name: sym for name, sym in zip(var_names, self.syms)}
        self.expr = sp.parse_expr(formula_str, local_dict=self.sym_dict)

    def diff(self, diff_var, order=1):
        s = self.sym_dict[diff_var]
        return sp.diff(self.expr, s, order)

    def diff_multi(self, *diff_vars):
        res = self.expr
        for v in diff_vars:
            s = self.sym_dict[v]
            res = sp.diff(res, s)
        return res

    def integral_indef(self, int_var):
        s = self.sym_dict[int_var]
        return sp.integrate(self.expr, s)

    def integral_def(self, int_var, lower, upper):
        s = self.sym_dict[int_var]
        return sp.integrate(self.expr, (s, lower, upper))

    def multi_integral_indef(self, *int_vars):
        res = self.expr
        for v in int_vars:
            s = self.sym_dict[v]
            res = sp.integrate(res, s)
        return res

    def multi_integral_def(self, int_var_list, limits_list):
        res = self.expr
        for v, (low, high) in zip(int_var_list, limits_list):
            s = self.sym_dict[v]
            res = sp.integrate(res, (s, low, high))
        return res

    def find_critical_points(self):
        grad = []
        for v in self.var_names:
            s = self.sym_dict[v]
            grad.append(sp.diff(self.expr, s))
        sol = sp.solve(grad, self.syms, dict=True)
        return sol

    def lagrange_multiplier(self, constraint_str):
        lam = sp.Symbol("lambda")
        g = sp.parse_expr(constraint_str, local_dict=self.sym_dict)
        L = self.expr - lam * g
        eq_list = []
        for v in self.var_names:
            s = self.sym_dict[v]
            eq_list.append(sp.diff(L, s))
        eq_list.append(g)
        sol = sp.solve(eq_list, [*self.syms, lam], dict=True)
        return sol

    def subs(self, expr, sub_dict):
        return expr.subs(sub_dict).evalf()

    def to_str(self, expr):
        return str(expr)


# ==================== UI 层 ====================
class App(tk.Tk):
    # 每种操作的参数输入字段：(标签, 默认值)  —— 默认值全部清空
    OP_FIELDS = {
        "diff":        [("求导变量", ""), ("求导阶数(留空=1)", "")],
        "diff_multi":  [("求导变量(逗号分隔)", "")],
        "indef":       [("积分变量", "")],
        "def":         [("积分变量", ""), ("积分下限(留空=0)", ""), ("积分上限(留空=1)", "")],
        "multi_indef": [("积分变量(逗号分隔)", "")],
        "multi_def":   [("积分变量(逗号分隔)", ""),
                        ("各下限(逗号分隔, 留空=0)", ""),
                        ("各上限(逗号分隔, 留空=1)", "")],
        "critical":    [],
        "lagrange":    [("约束 g=0", "")],
    }

    OP_HINT = {
        "diff": "单变量求导 / 高阶导数",
        "diff_multi": "多元混合偏导，例：x,y 代表 ∂²f/(∂x∂y)",
        "indef": "一重不定积分",
        "def": "一重定积分",
        "multi_indef": "多重不定积分（二重/三重）",
        "multi_def": "多重定积分（二重/三重定积分）",
        "critical": "求无约束驻点（所有一阶偏导=0）",
        "lagrange": "拉格朗日乘数法 条件极值（约束 g=0）",
    }

    def __init__(self):
        super().__init__()
        self.title("高数计算器")
        self.iconbitmap(resource_path("icon.ico"))
        self.geometry("980x720")
        self.minsize(860, 600)

        self.op_var = tk.StringVar(value="diff | 单变量求导 / 高阶导数")  # ← 原来缺这个

        self.history = []
        self.last_result = None
        self.last_show_expr = None
        self.sub_entries = {}

        self._build_ui()
        self.on_op_change()

    # ---------- 构建界面 ----------
    def _build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=10)
        left.pack(side="left", fill="both", expand=True)

        right = ttk.LabelFrame(main, text="历史记录", padding=6)
        right.pack(side="right", fill="y", padx=(0, 8), pady=8)

        # ---- 输入区 ----
        input_frame = ttk.LabelFrame(left, text="输入", padding=10)
        input_frame.pack(fill="x")

        ttk.Label(input_frame, text="函数表达式(乘号记得加*)：").grid(row=0, column=0, sticky="w")
        self.func_entry = ttk.Entry(input_frame)
        self.func_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(input_frame, text="变量(逗号分隔)：").grid(row=1, column=0, sticky="w")
        self.var_entry = ttk.Entry(input_frame, width=28)
        self.var_entry.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(input_frame, text="操作类型：").grid(row=1, column=2, sticky="e", padx=(10, 4))
        self.op_box = ttk.Combobox(
            input_frame, textvariable=self.op_var, state="readonly", width=26,
            values=[f"{k} | {v}" for k, v in self.OP_HINT.items()],
        )
        self.op_box.grid(row=1, column=3, sticky="w")
        self.op_box.bind("<<ComboboxSelected>>", self.on_op_change)

        input_frame.columnconfigure(1, weight=1)

        # ---- 参数区 ----
        self.param_frame = ttk.LabelFrame(left, text="参数", padding=10)
        self.param_frame.pack(fill="x", pady=8)
        self.param_entries = {}

        # ---- 按钮区 ----
        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="计算", command=self.calculate).pack(side="left", padx=4)
        ttk.Button(btns, text="清空结果", command=self.clear_result).pack(side="left", padx=4)
        ttk.Button(btns, text="复制结果", command=self.copy_result).pack(side="left", padx=4)

        # ---- 结果区 ----
        ttk.Label(left, text="计算结果：").pack(anchor="w")
        self.result_text = scrolledtext.ScrolledText(
            left, height=16, wrap="word", font=("Consolas", 11)
        )
        self.result_text.pack(fill="both", expand=True, pady=4)

        # ---- 参数代入区 ----
        self.sub_frame = ttk.LabelFrame(left, text="代入参数计算数值", padding=10)
        self.sub_frame.pack(fill="x", pady=4)

        # ---- 历史列表 ----
        self.history_list = tk.Listbox(right, width=30, height=32)
        self.history_list.pack(fill="both", expand=True)
        self.history_list.bind("<<ListboxSelect>>", self.on_history_select)
        ttk.Button(right, text="清空历史", command=self.clear_history).pack(fill="x", pady=4)

    # ---------- 切换操作类型 ----------
    def _current_op(self):
        text = self.op_var.get()
        return text.split("|")[0].strip() if text else "diff"

    def on_op_change(self, event=None):
        for w in self.param_frame.winfo_children():
            w.destroy()
        self.param_entries.clear()

        op = self._current_op()
        for i, (label, default) in enumerate(self.OP_FIELDS[op]):
            ttk.Label(self.param_frame, text=label + "：").grid(
                row=i, column=0, sticky="w", pady=3
            )
            e = ttk.Entry(self.param_frame, width=52)
            if default:                      # ← 默认值为空时不 insert
                e.insert(0, default)
            e.grid(row=i, column=1, sticky="w", pady=3)
            self.param_entries[label] = e

    # ---------- 小工具：非空校验 ----------
    @staticmethod
    def _need(val, name):
        val = val.strip()
        if not val:
            raise ValueError(f"{name}不能为空！")
        return val

    # ---------- 核心计算 ----------
    def calculate(self):
        try:
            op = self._current_op()
            is_indef = op in ("indef", "multi_indef")
            integral_vars = []

            func_str = self._need(self.func_entry.get(), "函数表达式")
            var_input = self._need(self.var_entry.get(), "变量列表")
            var_list = [v.strip() for v in var_input.split(",") if v.strip()]

            calc = SymbolCalc(func_str, var_list)
            p = {k: v.get().strip() for k, v in self.param_entries.items()}
            result = None

            if op == "diff":
                dv = self._need(p["求导变量"], "求导变量")
                order = int(p["求导阶数(留空=1)"] or 1)   # 留空默认 1
                result = calc.diff(dv, order)

            elif op == "diff_multi":
                dv_list = [v.strip() for v in
                           self._need(p["求导变量(逗号分隔)"], "求导变量").split(",")]
                result = calc.diff_multi(*dv_list)

            elif op == "indef":
                iv = self._need(p["积分变量"], "积分变量")
                integral_vars.append(iv)
                result = calc.integral_indef(iv)

            elif op == "def":
                iv = self._need(p["积分变量"], "积分变量")
                low_str = p["积分下限(留空=0)"].strip() or "0"
                high_str = p["积分上限(留空=1)"].strip() or "1"
                lower_sym = sp.parse_expr(low_str)
                upper_sym = sp.parse_expr(high_str)
                result = calc.integral_def(iv, lower_sym, upper_sym)

            elif op == "multi_indef":
                iv_list = [v.strip() for v in
                           self._need(p["积分变量(逗号分隔)"], "积分变量").split(",")]
                integral_vars.extend(iv_list)
                result = calc.multi_integral_indef(*iv_list)

            elif op == "multi_def":
                iv_list = [v.strip() for v in
                           self._need(p["积分变量(逗号分隔)"], "积分变量").split(",")]
                low_raw = p["各下限(逗号分隔, 留空=0)"].strip()
                high_raw = p["各上限(逗号分隔, 留空=1)"].strip()
                low_parts = [x.strip() for x in low_raw.split(",")] if low_raw else []
                high_parts = [x.strip() for x in high_raw.split(",")] if high_raw else []
                # 位数不够就用默认 0 / 1 补齐
                lows = [sp.parse_expr(low_parts[i] if i < len(low_parts) and low_parts[i] else "0")
                        for i in range(len(iv_list))]
                highs = [sp.parse_expr(high_parts[i] if i < len(high_parts) and high_parts[i] else "1")
                         for i in range(len(iv_list))]
                limits = list(zip(lows, highs))
                result = calc.multi_integral_def(iv_list, limits)

            elif op == "critical":
                result = calc.find_critical_points()

            elif op == "lagrange":
                con_str = self._need(p["约束 g=0"], "约束条件")
                result = calc.lagrange_multiplier(con_str)

            else:
                raise ValueError("操作类型错误！")

            self.last_result = result

            # ---- 不定积分加常数 ----
            if is_indef:
                if op == "indef":
                    show_expr = result + sp.Symbol("C")
                else:
                    var_num = len(integral_vars)
                    consts = [sp.symbols(f"C{i}") for i in range(1, var_num + 1)]
                    show_expr = result + sum(consts)
            else:
                show_expr = result
            self.last_show_expr = show_expr

            # ---- 输出 ----
            self.result_text.delete("1.0", "end")
            self.result_text.insert("end", "===== 计算结果 =====\n")
            self.result_text.insert("end", f"表达式：\n{sp.pretty(show_expr)}\n\n")
            self.result_text.insert("end", f"字符串形式：{calc.to_str(show_expr)}\n")

            # ---- 自由符号 / 常数 ----
            if isinstance(result, list):
                self.result_text.insert("end", "\n解集结果，跳过数值代入。\n")
                self._clear_sub_frame("（当前结果为解集，无法代入）")
            else:
                free_syms = [s for s in result.free_symbols if not str(s).startswith("C")]
                if free_syms:
                    self._build_sub_entries(free_syms)
                else:
                    num_res = result.evalf()
                    self.result_text.insert("end", f"\n表达式为常数，数值结果为：{num_res}\n")
                    self._clear_sub_frame("（结果为常数，无需代入）")

            # ---- 写历史 ----
            title = f"{op} | {func_str}"
            self.history.append((title, self.result_text.get("1.0", "end")))
            self.history_list.insert("end", title)
            self.history_list.see("end")

        except Exception as e:
            messagebox.showerror("错误", str(e))

    # ---------- 参数代入区 ----------
    def _clear_sub_frame(self, hint=""):
        for w in self.sub_frame.winfo_children():
            w.destroy()
        self.sub_entries.clear()
        if hint:
            ttk.Label(self.sub_frame, text=hint).pack(anchor="w")

    def _build_sub_entries(self, free_syms):
        self._clear_sub_frame()
        ttk.Label(self.sub_frame,
                  text="输入参数赋值，格式：a=2（留空表示不代入该符号）").pack(anchor="w")
        for s in free_syms:
            row = ttk.Frame(self.sub_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{s} =", width=8).pack(side="left")
            e = ttk.Entry(row, width=24)
            e.pack(side="left")
            self.sub_entries[s] = e
        ttk.Button(self.sub_frame, text="代入计算",
                   command=self.apply_subs).pack(anchor="w", pady=4)

    def apply_subs(self):
        if self.last_result is None:
            return
        try:
            sub_dict = {}
            for s, e in self.sub_entries.items():
                val = e.get().strip()
                if val:
                    sub_dict[s] = sp.parse_expr(val)
            if not sub_dict:
                messagebox.showinfo("提示", "没有输入任何赋值")
                return
            num_res = self.last_result.subs(sub_dict).evalf()
            self.result_text.insert("end", f"\n代入后数值结果：{num_res}\n")

            if self.history:
                title, _ = self.history[-1]
                self.history[-1] = (title, self.result_text.get("1.0", "end"))
        except Exception as e:
            messagebox.showerror("错误", str(e))

    # ---------- 历史 / 清空 / 复制 ----------
    def on_history_select(self, event):
        sel = self.history_list.curselection()
        if not sel:
            return
        idx = sel[0]
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", self.history[idx][1])

    def clear_history(self):
        self.history.clear()
        self.history_list.delete(0, "end")

    def clear_result(self):
        self.result_text.delete("1.0", "end")
        self.last_result = None
        self.last_show_expr = None
        self._clear_sub_frame("（计算后自动出现）")

    def copy_result(self):
        txt = self.result_text.get("1.0", "end").strip()
        if txt:
            self.clipboard_clear()
            self.clipboard_append(txt)
            messagebox.showinfo("提示", "结果已复制到剪贴板")


if __name__ == "__main__":
    App().mainloop()
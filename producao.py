import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import stats
import time
import random
import os

# =============================================================================
# 1. BANCO DE DADOS
# =============================================================================
DB_MATERIAIS = {
    "Aço SAE 1020":  {"fator_tempo": 1.0, "custo_kg": 9.50,  "densidade": 7.85, "dureza_fator": 1.0},
    "Aço SAE 1045":  {"fator_tempo": 1.4, "custo_kg": 14.20, "densidade": 7.85, "dureza_fator": 1.4},
    "Aço Inox 304":  {"fator_tempo": 2.5, "custo_kg": 38.00, "densidade": 8.00, "dureza_fator": 2.8},
    "Alumínio 6061": {"fator_tempo": 0.6, "custo_kg": 24.00, "densidade": 2.70, "dureza_fator": 0.5},
    "Latão CLA":     {"fator_tempo": 0.5, "custo_kg": 48.00, "densidade": 8.50, "dureza_fator": 0.4}
}
DB_ROSCAS = {
    "Métrica (M)":       {"fator_complexidade": 1.0, "stress": 1.0},
    "Trapezoidal (Tr)":  {"fator_complexidade": 1.8, "stress": 1.6},
    "Quadrada":          {"fator_complexidade": 1.7, "stress": 1.5}
}
DB_MAQUINAS = {
    "Torno CNC":    {"precisao": 0.005, "custo_hora": 85.00, "potencia": 15.0, "velocidade": 1.0, "setup_horas": 2.0},
    "Torno Manual": {"precisao": 0.060, "custo_hora": 45.00, "potencia": 5.0,  "velocidade": 0.35, "setup_horas": 0.5} 
}
DB_FERRAMENTAS = {
    "Sandvik (Premium)":  {"vida_util": 1.5, "custo": 85.00},
    "Iscar (Standard)":   {"vida_util": 1.0, "custo": 55.00},
    "Chinesa (Genérica)": {"vida_util": 0.5, "custo": 18.00}
}
OEE_EFICIENCIA = 0.85 

# =============================================================================
# 2. INTERFACE GRÁFICA
# =============================================================================

class SimuladorIndustrial(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly") 
        self.title("SAMC v7.3 - Versão Completa Corrigida")
        self.state('zoomed')
        
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=YES)

        self.sidebar = ttk.Frame(main_container, padding=20, bootstyle="secondary")
        self.sidebar.pack(side=LEFT, fill=Y)

        self.content = ttk.Frame(main_container, padding=10)
        self.content.pack(side=RIGHT, fill=BOTH, expand=YES)

        self.criar_sidebar()
        self.criar_area_conteudo()

    def criar_sidebar(self):
        lbl_brand = ttk.Label(self.sidebar, text="⚙️ PARÂMETROS", font=("Helvetica", 16, "bold"), bootstyle="inverse-secondary")
        lbl_brand.pack(pady=(0, 20))

        # --- Inputs ---
        lf_mat = ttk.Labelframe(self.sidebar, text=" 1. Comparativo ", padding=10, bootstyle="info")
        lf_mat.pack(fill=X, pady=5)
        ttk.Label(lf_mat, text="Material A", font=("Segoe UI", 9, "bold")).pack(anchor=W)
        self.cb_ma = ttk.Combobox(lf_mat, values=list(DB_MATERIAIS.keys()), state="readonly"); self.cb_ma.current(0); self.cb_ma.pack(fill=X, pady=5)
        ttk.Label(lf_mat, text="Material B", font=("Segoe UI", 9, "bold")).pack(anchor=W)
        self.cb_mb = ttk.Combobox(lf_mat, values=list(DB_MATERIAIS.keys()), state="readonly"); self.cb_mb.current(1); self.cb_mb.pack(fill=X)

        lf_geo = ttk.Labelframe(self.sidebar, text=" 2. Geometria ", padding=10, bootstyle="info")
        lf_geo.pack(fill=X, pady=5)
        f_dims = ttk.Frame(lf_geo)
        f_dims.pack(fill=X)
        ttk.Label(f_dims, text="Ø (mm)").pack(side=LEFT)
        self.ent_d = ttk.Entry(f_dims, width=6); self.ent_d.insert(0, "20.0"); self.ent_d.pack(side=LEFT, padx=5)
        ttk.Label(f_dims, text="Comp.").pack(side=LEFT)
        self.ent_c = ttk.Entry(f_dims, width=6); self.ent_c.insert(0, "80.0"); self.ent_c.pack(side=LEFT, padx=5)
        ttk.Label(lf_geo, text="Rosca").pack(anchor=W, pady=5)
        self.cb_r = ttk.Combobox(lf_geo, values=list(DB_ROSCAS.keys()), state="readonly"); self.cb_r.current(1); self.cb_r.pack(fill=X)

        lf_proc = ttk.Labelframe(self.sidebar, text=" 3. Processo ", padding=10, bootstyle="info")
        lf_proc.pack(fill=X, pady=5)
        self.cb_maq = ttk.Combobox(lf_proc, values=list(DB_MAQUINAS.keys()), state="readonly"); self.cb_maq.current(0); self.cb_maq.pack(fill=X, pady=5)
        self.cb_fer = ttk.Combobox(lf_proc, values=list(DB_FERRAMENTAS.keys()), state="readonly"); self.cb_fer.current(1); self.cb_fer.pack(fill=X)

        lf_com = ttk.Labelframe(self.sidebar, text=" 4. Comercial ", padding=10, bootstyle="info")
        lf_com.pack(fill=X, pady=5)
        ttk.Label(lf_com, text="Lote").pack(anchor=W)
        self.ent_q = ttk.Entry(lf_com); self.ent_q.insert(0, "1000"); self.ent_q.pack(fill=X, pady=5)
        ttk.Label(lf_com, text="Venda (R$)").pack(anchor=W)
        self.ent_p = ttk.Entry(lf_com); self.ent_p.insert(0, "18.00"); self.ent_p.pack(fill=X)

        ttk.Separator(self.sidebar).pack(fill=X, pady=15)
        self.btn_run = ttk.Button(self.sidebar, text="▶ RODAR SIMULAÇÃO", bootstyle="success", command=self.iniciar_animacao)
        self.btn_run.pack(fill=X, ipady=5)
        self.btn_save = ttk.Button(self.sidebar, text="💾 SALVAR", bootstyle="secondary-outline", command=self.salvar_laudo)
        self.btn_save.pack(fill=X, pady=10)

    def criar_area_conteudo(self):
        self.notebook = ttk.Notebook(self.content, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES)

        # ABA 1: RELATÓRIO
        self.tab_report = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_report, text=" 📄 Laudo Gerencial ")
        self.txt_rep = tk.Text(self.tab_report, font=("Consolas", 11), relief="flat", padx=15, pady=15, bg="#f8f9fa")
        self.txt_rep.pack(fill=BOTH, expand=YES)

        # ABA 2: DADOS (COM ORDENAÇÃO)
        self.tab_data = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_data, text=" 📊 Dados (Tabela) ")
        
        # Colunas expandidas
        cols = ["ID", "Material", "Medida", "Temp", "Defeitos", "Tempo (s)", "Energia (Wh)"]
        self.tree = ttk.Treeview(self.tab_data, columns=cols, show="headings", bootstyle="info")
        
        # Configurar colunas e BIND para ordenar ao clicar
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.ordenar_tabela(c, False))
            self.tree.column(col, width=100, anchor="center")
            
        self.tree.pack(fill=BOTH, expand=YES)
        
        lbl_hint = ttk.Label(self.tab_data, text="* Clique no título da coluna para ordenar Crescente/Decrescente", font=("Arial", 9, "italic"))
        lbl_hint.pack(pady=5)

        # ABA 3: GRÁFICOS
        self.tab_graphs = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_graphs, text=" 📈 Gráficos ")

    # --- FUNÇÃO DE ORDENAÇÃO ---
    def ordenar_tabela(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.ordenar_tabela(col, not reverse))

    # =========================================================================
    # LÓGICA E ANIMAÇÃO
    # =========================================================================

    def iniciar_animacao(self):
        try:
            ma, mb = self.cb_ma.get(), self.cb_mb.get()
            if ma == mb: messagebox.showwarning("!", "Materiais iguais."); return
            float(self.ent_d.get()), float(self.ent_c.get()), int(self.ent_q.get()), float(self.ent_p.get())
        except: messagebox.showerror("Erro", "Campos inválidos."); return

        self.loading_win = tk.Toplevel(self)
        self.loading_win.title("Loading")
        w, h = 300, 200
        x = (self.winfo_screenwidth()//2) - (w//2)
        y = (self.winfo_screenheight()//2) - (h//2)
        self.loading_win.geometry(f"{w}x{h}+{x}+{y}")
        self.loading_win.overrideredirect(True)
        
        frm = ttk.Frame(self.loading_win, bootstyle="secondary", padding=2)
        frm.pack(fill=BOTH, expand=YES)
        inner = ttk.Frame(frm, padding=20, bootstyle="light")
        inner.pack(fill=BOTH, expand=YES)
        
        ttk.Label(inner, text="⚙️", font=("Arial", 50), bootstyle="inverse-light").pack(pady=10)
        self.lbl_status = ttk.Label(inner, text="Iniciando...", font=("Arial", 10), bootstyle="inverse-light")
        self.lbl_status.pack(pady=5)
        
        pb = ttk.Progressbar(inner, mode='indeterminate', bootstyle="success-striped")
        pb.pack(fill=X, pady=10)
        pb.start(10)

        self.btn_run.configure(state="disabled")
        self.after(1000, lambda: self.lbl_status.config(text="Medindo Tempos..."))
        self.after(2500, lambda: self.lbl_status.config(text="Analisando Energia..."))
        self.after(4000, lambda: self.lbl_status.config(text="Calculando Teste T..."))
        self.after(5000, self.executar_simulacao_real)

    def executar_simulacao_real(self):
        if hasattr(self, 'loading_win'): self.loading_win.destroy()
        self.btn_run.configure(state="normal")
        self.rodar_logica()

    def calcular(self, mat, maq, fer, rosca, d, c, q):
        dm, dmq, dfr, dr = DB_MATERIAIS[mat], DB_MAQUINAS[maq], DB_FERRAMENTAS[fer], DB_ROSCAS[rosca]
        tempo_base = ((d*1.5) + (c*2.0) + (d*c*0.05))
        tempo_ciclo = tempo_base * dm['fator_tempo'] * dr['fator_complexidade'] * (1/dmq['velocidade']) + 25
        tempo_ciclo = tempo_ciclo / OEE_EFICIENCIA
        tempo_total = ((tempo_ciclo * q) / 3600) + dmq['setup_horas']
        
        peso = (3.1416*((d/20)**2)*(c/10) * dm['densidade'] / 1000) * q
        c_mat = peso * dm['custo_kg']
        c_maq = tempo_total * dmq['custo_hora']
        
        vida = (15.0 * dfr['vida_util']) / (dm['dureza_fator'] * dr['stress'])
        pastilhas = int(np.ceil(((tempo_ciclo*q)/3600) / vida))
        c_fer = pastilhas * dfr['custo']
        
        return { "tempo": tempo_total, "c_mat": c_mat, "c_maq": c_maq, "c_fer": c_fer, "c_tot": c_mat+c_maq+c_fer, "pastilhas": pastilhas, "precisao": dmq['precisao'] }

    def rodar_logica(self):
        ma, mb = self.cb_ma.get(), self.cb_mb.get()
        maq_user, fer, rosca = self.cb_maq.get(), self.cb_fer.get(), self.cb_r.get()
        d, c, q = float(self.ent_d.get()), float(self.ent_c.get()), int(self.ent_q.get())
        pv = float(self.ent_p.get())

        ra = self.calcular(ma, maq_user, fer, rosca, d, c, q)
        rb = self.calcular(mb, maq_user, fer, rosca, d, c, q)

        # Recomendação
        maq_alt = "Torno Manual" if maq_user == "Torno CNC" else "Torno CNC"
        ra_alt = self.calcular(ma, maq_alt, fer, rosca, d, c, q)
        recomendacao = None
        if ra_alt['c_tot'] < ra['c_tot']:
            economia = ra['c_tot'] - ra_alt['c_tot']
            recomendacao = {'msg': f"💡 DICA DE OURO: Usar '{maq_alt}' seria R$ {economia:.2f} mais barato!", 'tipo': 'economica'}

        # Geração de Dados Aleatórios
        np.random.seed(int(time.time()))
        causa_real = random.choice(['TERMICA', 'VIBRACAO'])
        
        da = np.random.normal(d, ra['precisao'], q)
        db = np.random.normal(d, rb['precisao']*1.1, q)
        
        ta = np.random.normal(60, 5, q)
        tb = np.random.normal(80, 8, q)

        if causa_real == 'TERMICA':
            def_a = (ta * 0.15) + np.random.normal(0, 0.5, q)
            def_b = (tb * 0.20) + np.random.normal(0, 0.5, q)
        else:
            def_a = np.random.normal(10, 3, q)
            def_b = np.random.normal(12, 4, q)

        # Cálculo de Tempo e Energia Individual pra tabela
        tempo_med_a = (ra['tempo'] * 3600) / q
        tempo_a_ind = np.random.normal(tempo_med_a, 2.0, q) 
        pot_a = DB_MAQUINAS[maq_user]['potencia'] * (0.5 if "CNC" in maq_user else 0.4)
        ener_a_ind = (tempo_a_ind/3600) * pot_a * 1000 

        tempo_med_b = (rb['tempo'] * 3600) / q
        tempo_b_ind = np.random.normal(tempo_med_b, 2.0, q)
        ener_b_ind = (tempo_b_ind/3600) * pot_a * 1000

        # Estatística
        slope, intercept, r_val, p_val, stderr = stats.linregress(np.concatenate([ta, tb]), np.concatenate([def_a, def_b]))
        r_squared = r_val**2
        
        # TESTE T DE STUDENT
        t_stat, p_val_ttest = stats.ttest_ind(da, db)

        self.atualizar_tabela(q, ma, mb, da, ta, def_a, tempo_a_ind, ener_a_ind, db, tb, def_b, tempo_b_ind, ener_b_ind)
        self.gerar_graficos(da, db, ma, mb, d, np.concatenate([ta, tb]), np.concatenate([def_a, def_b]), slope, intercept, r_squared)
        self.gerar_relatorio_bonito(q, maq_user, rosca, ma, mb, ra, rb, pv, da, db, r_squared, p_val_ttest, recomendacao, causa_real)
        self.notebook.select(0)

    def atualizar_tabela(self, q, ma, mb, da, ta, def_a, t_a, e_a, db, tb, def_b, t_b, e_b):
        for i in self.tree.get_children(): self.tree.delete(i)
        for i in range(min(q, 50)):
            self.tree.insert("", "end", values=(f"A-{i}", ma, f"{da[i]:.3f}", f"{ta[i]:.1f}", f"{def_a[i]:.2f}", f"{t_a[i]:.1f}", f"{e_a[i]:.1f}"))
            self.tree.insert("", "end", values=(f"B-{i}", mb, f"{db[i]:.3f}", f"{tb[i]:.1f}", f"{def_b[i]:.2f}", f"{t_b[i]:.1f}", f"{e_b[i]:.1f}"))

    def gerar_graficos(self, da, db, ma, mb, alvo, t_all, def_all, slope, intercept, r2):
        for w in self.tab_graphs.winfo_children(): w.destroy()
        
        fig = plt.Figure(figsize=(10, 5), dpi=100)
        fig.patch.set_facecolor('#ffffff')

        ax1 = fig.add_subplot(121)
        ax1.hist(da, bins=20, alpha=0.6, label="Mat A", color='#2980b9')
        ax1.hist(db, bins=20, alpha=0.6, label="Mat B", color='#e67e22')
        ax1.axvline(alvo, color='red', linestyle='--')
        ax1.set_title("Comparativo de Precisão (Histograma)", fontsize=10, fontweight='bold')
        ax1.legend()

        ax2 = fig.add_subplot(122)
        ax2.scatter(t_all, def_all, alpha=0.4, color='gray', s=15)
        x_vals = np.linspace(min(t_all), max(t_all), 100)
        ax2.plot(x_vals, intercept + slope * x_vals, 'r', linewidth=2, label=f'R²={r2:.2f}')
        ax2.set_title("Regressão: Temp vs Defeitos", fontsize=10, fontweight='bold')
        ax2.set_xlabel("Temperatura")
        ax2.set_ylabel("Defeitos")
        ax2.legend()

        fig.tight_layout(pad=3.0)
        canv = FigureCanvasTkAgg(fig, master=self.tab_graphs)
        canv.draw()
        canv.get_tk_widget().pack(fill=BOTH, expand=YES, padx=10, pady=10)

    # =========================================================================
    # RELATÓRIO COMPLETO
    # =========================================================================

    def gerar_relatorio_bonito(self, q, maq, rosca, ma, mb, ra, rb, pv, da, db, r2, p_val_ttest, recomendacao, causa_real):
        t = self.txt_rep
        t.configure(state='normal'); t.delete(1.0, tk.END)
        t.configure(tabs=(250, 450))

        # Estilos
        t.tag_configure("TITLE", font=("Segoe UI", 18, "bold"), foreground="#2c3e50", justify="center", spacing3=15)
        t.tag_configure("SUBINFO", font=("Segoe UI", 10), foreground="#7f8c8d", justify="center", spacing3=20)
        t.tag_configure("HEADER_BG", font=("Segoe UI", 11, "bold"), foreground="white", background="#3498db", spacing1=10, spacing3=10, lmargin1=10)
        t.tag_configure("BOLD", font=("Segoe UI", 10, "bold"), foreground="#2c3e50")
        t.tag_configure("NORMAL", font=("Segoe UI", 10), foreground="#34495e", lmargin1=10)
        t.tag_configure("GREEN", foreground="#27ae60", font=("Segoe UI", 10, "bold"))
        t.tag_configure("RED", foreground="#c0392b", font=("Segoe UI", 10, "bold"))
        t.tag_configure("TIP", font=("Segoe UI", 10, "bold"), foreground="#d35400", background="#fad7a0", lmargin1=10)
        t.tag_configure("HR", font=("Arial", 1), background="#ecf0f1")

        t.insert(tk.END, "LAUDO TÉCNICO DE ENGENHARIA\n", "TITLE")
        t.insert(tk.END, f"LOTE: {q} un. | MÁQUINA: {maq} | ROSCA: {rosca}\n", "SUBINFO")

        t.insert(tk.END, "  1. ANÁLISE DE CUSTOS INDUSTRIAIS  \n", "HEADER_BG"); t.insert(tk.END, "\n")
        t.insert(tk.END, f"PARÂMETRO\t{ma}\t{mb}\n", "BOLD")
        t.insert(tk.END, " " * 120 + "\n", "HR")
        t.insert(tk.END, f"Tempo Total:\t{ra['tempo']:.2f} h\t{rb['tempo']:.2f} h\n", "NORMAL")
        t.insert(tk.END, f"Consumo Pastilhas:\t{ra['pastilhas']} un.\t{rb['pastilhas']} un.\n", "NORMAL")
        t.insert(tk.END, f"Custo Máquina+Setup:\tR$ {ra['c_maq']:.2f}\tR$ {rb['c_maq']:.2f}\n", "NORMAL")
        t.insert(tk.END, " " * 120 + "\n", "HR")
        t.insert(tk.END, f"CUSTO UNITÁRIO:\tR$ {ra['c_tot']/q:.2f}\tR$ {rb['c_tot']/q:.2f}\n", "BOLD")

        t.insert(tk.END, "\n  2. VIABILIDADE FINANCEIRA  \n", "HEADER_BG"); t.insert(tk.END, "\n")
        la, lb = (pv*q) - ra['c_tot'], (pv*q) - rb['c_tot']
        t.insert(tk.END, f"Res. {ma}:\t", "NORMAL"); t.insert(tk.END, f"R$ {la:.2f} [{'LUCRO' if la>0 else 'PREJUÍZO'}]\n", "GREEN" if la>0 else "RED")
        t.insert(tk.END, f"Res. {mb}:\t", "NORMAL"); t.insert(tk.END, f"R$ {lb:.2f} [{'LUCRO' if lb>0 else 'PREJUÍZO'}]\n", "GREEN" if lb>0 else "RED")

        sug_a = (ra['c_tot']/q) * 1.45
        t.insert(tk.END, f"\n>>> Preço Sugerido ({ma}): R$ {sug_a:.2f} (Margem 45%)\n", "TIP")

        t.insert(tk.END, "\n  3. DIAGNÓSTICO & ESTATÍSTICA  \n", "HEADER_BG"); t.insert(tk.END, "\n")
        
        interp_ttest = "Qualidade Similar" if p_val_ttest > 0.05 else "Diferença Significativa"
        t.insert(tk.END, f"Teste T Student:\tP-valor = {p_val_ttest:.4f}\n", "BOLD")
        t.insert(tk.END, f"Conclusão Teste T:\t{interp_ttest}\n\n", "NORMAL")
        
        t.insert(tk.END, f"R² (Defeitos):\t{r2:.4f}\n", "BOLD")
        diag = "Alta correlação (Térmica)" if r2 > 0.6 else "Baixa correlação (Vibração)"
        t.insert(tk.END, f"Diagnóstico:\t{diag}\n", "NORMAL")

        t.insert(tk.END, "\n  4. PARECER TÉCNICO & IA  \n", "HEADER_BG")
        best = ma if ra['c_tot'] < rb['c_tot'] else mb
        t.insert(tk.END, f"\n• Material Recomendado: {best}\n", "NORMAL")
        if recomendacao: t.insert(tk.END, f"\n{recomendacao['msg']}\n", "TIP")

        t.configure(state='disabled')

    def salvar_laudo(self):
        # 1. Define o nome da pasta
        pasta_nome = "Relatorios_SAMC"
        
        # 2. Cria a pasta se ela não existir 
        if not os.path.exists(pasta_nome):
            os.makedirs(pasta_nome)

        # 3. Pega o texto do relatório
        txt = self.txt_rep.get(1.0, tk.END)
        if len(txt) < 10: 
            messagebox.showwarning("Aviso", "Não há relatório gerado para salvar.")
            return

        # 4. Abre a janela de salvar JÁ DENTRO da pasta criada
        # Gera um nome de arquivo sugestivo com data/hora para não substituir
        nome_arquivo_sugerido = f"Laudo_{int(time.time())}.txt"
        
        f = filedialog.asksaveasfilename(
            initialdir=pasta_nome,  # Força abrir na pasta correta
            initialfile=nome_arquivo_sugerido,
            defaultextension=".txt", 
            filetypes=[("Texto", "*.txt")]
        )
        
        if f:
            with open(f, "w", encoding="utf-8") as file: file.write(txt)
            messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{f}")
if __name__ == "__main__":
    app = SimuladorIndustrial()

    app.mainloop()

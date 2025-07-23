import io
import os
from tkinter import colorchooser, filedialog

import customtkinter as ctk
import qrcode
from PIL import Image, ImageColor, ImageTk
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import (
    CircleModuleDrawer,
    GappedSquareModuleDrawer,
    RoundedModuleDrawer,
    SquareModuleDrawer,
)

try:
    from brcode import Pix
    HAS_PIX = True
except ImportError:
    HAS_PIX = False

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

def get_wifi_string(ssid, password, security):
    return f"WIFI:T:{security};S:{ssid};P:{password};;"

def get_tel_string(tel):
    return f"tel:{tel}"

def get_mailto_string(email):
    return f"mailto:{email}"

def get_vcard_string(name, phone, email):
    return f"BEGIN:VCARD\nVERSION:3.0\nN:{name}\nTEL:{phone}\nEMAIL:{email}\nEND:VCARD"

def get_pix_string(chave, nome, cidade, valor):
    if HAS_PIX:
        try:
            pix = Pix(
                key=chave,
                name=nome,
                city=cidade,
                amount=float(valor) if valor else None
            )
            return pix.payload()
        except Exception:
            return f"PIX:{chave}|NOME:{nome}|CIDADE:{cidade}|VALOR:{valor}"
    else:
        return f"PIX:{chave}|NOME:{nome}|CIDADE:{cidade}|VALOR:{valor}"

def gerar_qrcode(
        data,
        size=400,
        fg_color="#FFFFFF",
        bg_color="#000000",
        border=4,
        module_style="quadrado",
        logo_path=None,
        auto_resize_logo=True,
        error_correction='H',
        box_size=10
    ):
    MODS = {
        "quadrado": SquareModuleDrawer(),
        "gapped": GappedSquareModuleDrawer(),
        "circulo": CircleModuleDrawer(),
        "arredondado": RoundedModuleDrawer()
    }
    drawer = MODS.get(module_style, SquareModuleDrawer())

    EC_DICT = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H,
    }

    qr = qrcode.QRCode(
        version=None,
        error_correction=EC_DICT.get(error_correction, qrcode.constants.ERROR_CORRECT_H),
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    fg_rgb = ImageColor.getrgb(fg_color)
    bg_rgb = ImageColor.getrgb(bg_color)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer,
        color_mask=SolidFillColorMask(fg_rgb, bg_rgb),
    ).convert("RGBA")

    img = img.resize((size, size), Image.LANCZOS)

    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            if auto_resize_logo:
                factor = 0.20
                w, h = img.size
                lw = int(w * factor)
                logo = logo.resize((lw, lw), Image.LANCZOS)
            px, py = (img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2
            img.alpha_composite(logo, (px, py))
        except Exception:
            pass

    return img

class QRCodeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de QR Code")
        self.geometry("950x680")
        self.minsize(700, 480)
        self.logo_path = None
        self.qr_img_pil = None
        self.mode = "light"
        self.fg_color = "#FFFFFF"
        self.bg_color = "#000000"

        # Novos parâmetros
        self.error_correction_var = ctk.StringVar(value="Máxima (H)")
        self.box_size_var = ctk.IntVar(value=10)
        self.size_var = ctk.IntVar(value=400)

        self._build_ui()
        self._bind_resize()

    def _build_ui(self):
        topbar = ctk.CTkFrame(self, fg_color="transparent", height=56)
        topbar.pack(fill="x", side="top")

        logo = ctk.CTkLabel(topbar, text="🔲", font=ctk.CTkFont(size=30))
        logo.pack(side="left", padx=(14,8))
        title = ctk.CTkLabel(topbar, text="Gerador de QR Code", font=ctk.CTkFont(size=23, weight="bold"))
        title.pack(side="left", padx=(0,16))
        theme_btn = ctk.CTkButton(
            topbar,
            width=48,
            text="☀️" if self.mode=="light" else "🌙",
            command=self._toggle_theme,
            fg_color="transparent",
            hover_color="#10B981"
        )
        theme_btn.pack(side="right", padx=20, pady=12)
        self.theme_btn = theme_btn

        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=(0,10))
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=3)
        main.rowconfigure(0, weight=1)

        left_scroll = ctk.CTkScrollableFrame(main, corner_radius=20, label_text=None)
        left_scroll.grid(row=0, column=0, sticky="nswe", padx=(0,16), pady=8)
        left_scroll.columnconfigure(0, weight=1)
        left = left_scroll  # para o resto do código funcionar igual
        row = 0
        tipo_lbl = ctk.CTkLabel(left, text="Tipo de QR Code", anchor="w")
        tipo_lbl.grid(row=row, column=0, sticky="we", padx=12, pady=(18,2))
        row += 1

        self.tipo_var = ctk.StringVar(value="Texto")
        tipo_cmb = ctk.CTkComboBox(
            left,
            variable=self.tipo_var,
            values=["Texto", "URL", "Telefone", "WiFi", "E-mail", "Contato (vCard)", "PIX"],
            command=self._atualizar_campos
        )
        tipo_cmb.grid(row=row, column=0, sticky="we", padx=12, pady=6)
        row += 1

        self.dyn_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.dyn_frame.grid(row=row, column=0, sticky="we", padx=4, pady=2)
        self.dyn_frame.columnconfigure(0, weight=1)
        self._criar_campos_dinamicos("Texto")
        row += 1

        ctk.CTkLabel(left, text="Personalização", anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="we", padx=12, pady=(16,2))
        row += 1

        # COR DOS QUADRADINHOS (PRETO) - deve alterar o BG do QR
        self.fg_color_btn = ctk.CTkButton(left, text="Cor dos Quadradinhos (preto)", command=lambda:self._pick_color('bg'))
        self.fg_color_btn.grid(row=row, column=0, sticky="we", padx=12, pady=6)
        row += 1
        self.fg_color_preview = ctk.CTkLabel(self.fg_color_btn, width=20, height=20, text="", corner_radius=10)
        self.fg_color_preview.place(relx=0.92, rely=0.5, anchor="center")

        # COR DE FUNDO (BRANCO) - deve alterar o FG do QR
        self.bg_color_btn = ctk.CTkButton(left, text="Cor de Fundo (branco)", command=lambda:self._pick_color('fg'))
        self.bg_color_btn.grid(row=row, column=0, sticky="we", padx=12, pady=6)
        row += 1
        self.bg_color_preview = ctk.CTkLabel(self.bg_color_btn, width=20, height=20, text="", corner_radius=10)
        self.bg_color_preview.place(relx=0.92, rely=0.5, anchor="center")

        ctk.CTkLabel(left, text="Formato dos Módulos", anchor="w").grid(row=row, column=0, sticky="we", padx=12, pady=(14,2))
        row += 1

        self.mod_style_var = ctk.StringVar(value="quadrado")
        mod_cmb = ctk.CTkComboBox(
            left, variable=self.mod_style_var,
            values=["quadrado","arredondado","circulo","gapped"]
        )
        mod_cmb.grid(row=row, column=0, sticky="we", padx=12, pady=6)
        row += 1

        # Tamanho do QR
        ctk.CTkLabel(left, text="Tamanho do QR", anchor="w").grid(row=row, column=0, sticky="we", padx=12, pady=(14,2))
        row += 1
        self.size_slider = ctk.CTkSlider(left, from_=128, to=1024, variable=self.size_var)
        self.size_slider.grid(row=row, column=0, sticky="we", padx=16, pady=6)
        row += 1

        # CORREÇÃO DE ERRO
        ctk.CTkLabel(left, text="Nível de Correção de Erro", anchor="w").grid(row=row, column=0, sticky="we", padx=12, pady=(14,2))
        row += 1
        ec_combo = ctk.CTkComboBox(left,
            values=["Baixa (L)", "Média (M)", "Alta (Q)", "Máxima (H)"],
            variable=self.error_correction_var
        )
        ec_combo.grid(row=row, column=0, sticky="we", padx=12, pady=6)
        row += 1

        # BOX_SIZE
        ctk.CTkLabel(left, text="Tamanho da Caixinha (box_size)", anchor="w").grid(row=row, column=0, sticky="we", padx=12, pady=(14,2))
        row += 1
        self.boxsize_slider = ctk.CTkSlider(left, from_=5, to=20, variable=self.box_size_var, number_of_steps=15)
        self.boxsize_slider.grid(row=row, column=0, sticky="we", padx=16, pady=6)
        row += 1

        ctk.CTkLabel(left, text="Logo ao Centro", anchor="w").grid(row=row, column=0, sticky="we", padx=12, pady=(14,2))
        row += 1

        logo_btn = ctk.CTkButton(left, text="Adicionar logo ⬆️", command=self._selecionar_logo)
        logo_btn.grid(row=row, column=0, sticky="we", padx=12, pady=6)
        row += 1

        self.logo_preview = ctk.CTkLabel(left, text="(sem logo)", anchor="center")
        self.logo_preview.grid(row=row, column=0, sticky="we", padx=12, pady=6)
        row += 1

        self.auto_resize_logo = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left, text="Redimensionar logo", variable=self.auto_resize_logo).grid(row=row, column=0, sticky="w", padx=18, pady=2)
        row += 1

        ctk.CTkLabel(left, text="Borda do QR", anchor="w").grid(row=row, column=0, sticky="we", padx=12, pady=(16,2))
        row += 1

        self.border_var = ctk.IntVar(value=4)
        border_slider = ctk.CTkSlider(left, from_=1, to=10, variable=self.border_var, number_of_steps=9)
        border_slider.grid(row=row, column=0, sticky="we", padx=16, pady=(0,8))
        row += 1

        # Painel direito (preview)
        right = ctk.CTkFrame(main, corner_radius=20)
        right.grid(row=0, column=1, sticky="nswe", padx=(0,4), pady=8)
        right.columnconfigure(0, weight=1)

        preview_card = ctk.CTkFrame(right, fg_color="#fff", corner_radius=18)
        preview_card.grid(row=0, column=0, sticky="nwe", padx=32, pady=(30,12))
        preview_card.columnconfigure(0, weight=1)
        preview_card.rowconfigure(0, weight=1)
        preview_card.rowconfigure(1, weight=1)

        self.preview_label = ctk.CTkLabel(preview_card, text="Preview", anchor="center", font=ctk.CTkFont(size=16, slant="italic"))
        self.preview_label.grid(row=0, column=0, padx=40, pady=(22,8), sticky="nsew")
        self.preview_canvas = ctk.CTkLabel(preview_card, text="", anchor="center")
        self.preview_canvas.grid(row=1, column=0, padx=28, pady=(0,22), sticky="nsew")

        btns = ctk.CTkFrame(right, fg_color="transparent")
        btns.grid(row=1, column=0, sticky="ew", padx=34, pady=(10,4))
        btns.columnconfigure((0,1,2,3), weight=1)

        gerar_btn = ctk.CTkButton(btns, text="Gerar QR Code", command=self._gerar, fg_color="#3B82F6", height=38, font=ctk.CTkFont(size=15, weight="bold"))
        gerar_btn.grid(row=0, column=0, columnspan=4, sticky="ew", pady=3)
        self.save_btn = ctk.CTkButton(btns, text="Salvar QR", fg_color="#10B981", command=self._salvar, state="disabled")
        self.save_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        self.copy_btn = ctk.CTkButton(btns, text="Copiar", command=self._copiar, state="disabled")
        self.copy_btn.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        self.limpar_btn = ctk.CTkButton(btns, text="Limpar", command=self._limpar, fg_color="#F59E42")
        self.limpar_btn.grid(row=1, column=2, sticky="ew", padx=2, pady=2)

        self.msg_label = ctk.CTkLabel(right, text="", anchor="center", font=ctk.CTkFont(size=12))
        self.msg_label.grid(row=2, column=0, pady=(10,4))
        self._update_color_previews()

    def _bind_resize(self):
        self.bind("<Configure>", lambda e: self._update_preview_img())

    def _toggle_theme(self):
        mode = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        ctk.set_appearance_mode(mode)
        self.mode = mode
        self.theme_btn.configure(text="☀️" if mode=="light" else "🌙")

    def _criar_campos_dinamicos(self, tipo):
        for w in self.dyn_frame.winfo_children():
            w.destroy()
        self.campos_dyn = {}

        def grid_dyn(widget, row, h=38):
            widget.grid(row=row, column=0, sticky="we", padx=6, pady=4)
            widget.configure(height=h)

        if tipo == "Texto":
            entry = ctk.CTkEntry(self.dyn_frame, placeholder_text="Digite o texto para o QR Code", height=38)
            grid_dyn(entry, 0, h=38)
            self.campos_dyn["text"] = entry

        elif tipo == "URL":
            entry = ctk.CTkEntry(self.dyn_frame, placeholder_text="Cole ou digite uma URL (https://...)", height=38)
            grid_dyn(entry, 0, h=38)
            self.campos_dyn["url"] = entry

        elif tipo == "Telefone":
            entry = ctk.CTkEntry(self.dyn_frame, placeholder_text="Digite o telefone (com DDD)", height=38)
            grid_dyn(entry, 0, h=38)
            self.campos_dyn["tel"] = entry

        elif tipo == "WiFi":
            ssid = ctk.CTkEntry(self.dyn_frame, placeholder_text="SSID (nome da rede)", height=32)
            grid_dyn(ssid, 0, h=32)
            password = ctk.CTkEntry(self.dyn_frame, placeholder_text="Senha", height=32)
            grid_dyn(password, 1, h=32)
            crypto = ctk.CTkComboBox(self.dyn_frame, values=["WPA", "WEP", "nopass"])
            crypto.set("WPA")
            crypto.grid(row=2, column=0, sticky="we", padx=6, pady=3)
            self.campos_dyn["ssid"] = ssid
            self.campos_dyn["password"] = password
            self.campos_dyn["crypto"] = crypto

        elif tipo == "E-mail":
            entry = ctk.CTkEntry(self.dyn_frame, placeholder_text="Digite o e-mail", height=38)
            grid_dyn(entry, 0, h=38)
            self.campos_dyn["email"] = entry

        elif tipo == "Contato (vCard)":
            name = ctk.CTkEntry(self.dyn_frame, placeholder_text="Nome", height=32)
            grid_dyn(name, 0, h=32)
            tel = ctk.CTkEntry(self.dyn_frame, placeholder_text="Telefone", height=32)
            grid_dyn(tel, 1, h=32)
            email = ctk.CTkEntry(self.dyn_frame, placeholder_text="E-mail", height=32)
            grid_dyn(email, 2, h=32)
            self.campos_dyn["name"] = name
            self.campos_dyn["tel"] = tel
            self.campos_dyn["email"] = email

        elif tipo == "PIX":
            chave = ctk.CTkEntry(self.dyn_frame, placeholder_text="Chave PIX (e-mail, tel, CPF...)", height=32)
            grid_dyn(chave, 0, h=32)
            nome = ctk.CTkEntry(self.dyn_frame, placeholder_text="Nome do beneficiário", height=32)
            grid_dyn(nome, 1, h=32)
            cidade = ctk.CTkEntry(self.dyn_frame, placeholder_text="Cidade", height=32)
            grid_dyn(cidade, 2, h=32)
            valor = ctk.CTkEntry(self.dyn_frame, placeholder_text="Valor (opcional)", height=32)
            grid_dyn(valor, 3, h=32)
            self.campos_dyn["chave"] = chave
            self.campos_dyn["nome"] = nome
            self.campos_dyn["cidade"] = cidade
            self.campos_dyn["valor"] = valor

    def _update_color_previews(self):
        # "Cor dos Quadradinhos" = self.bg_color
        # "Cor de Fundo" = self.fg_color
        self.fg_color_preview.configure(bg_color=self.bg_color)
        self.bg_color_preview.configure(bg_color=self.fg_color)


    def _atualizar_campos(self, event=None):
        self._criar_campos_dinamicos(self.tipo_var.get())
        self._limpar_preview()

    def _pick_color(self, which):
        rgb_tuple, hex_color = colorchooser.askcolor(title="Escolha a cor")
        color = hex_color
        if not color and rgb_tuple:
            color = '#%02x%02x%02x' % tuple(map(int, rgb_tuple))
        if color and isinstance(color, str) and len(color) == 7 and color.startswith("#"):
            color = color.lower()
            if which == 'fg':
                self.fg_color = color   # Cor de fundo do QR
            elif which == 'bg':
                self.bg_color = color   # Cor dos quadradinhos
            self._update_color_previews()
            self._update_preview_img()


    def _selecionar_logo(self):
        filetypes = [("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif"),("Todos arquivos","*.*")]
        path = filedialog.askopenfilename(title="Selecione o logo", filetypes=filetypes)
        if path:
            self.logo_path = path
            self.logo_preview.configure(text=os.path.basename(path))
            self._update_preview_img()

    def _obter_dados(self):
        tipo = self.tipo_var.get()
        campos = self.campos_dyn
        if tipo == "Texto":
            return campos["text"].get()
        elif tipo == "URL":
            return campos["url"].get()
        elif tipo == "Telefone":
            return get_tel_string(campos["tel"].get())
        elif tipo == "WiFi":
            return get_wifi_string(campos["ssid"].get(), campos["password"].get(), campos["crypto"].get())
        elif tipo == "E-mail":
            return get_mailto_string(campos["email"].get())
        elif tipo == "Contato (vCard)":
            return get_vcard_string(campos["name"].get(), campos["tel"].get(), campos["email"].get())
        elif tipo == "PIX":
            return get_pix_string(campos["chave"].get(), campos["nome"].get(), campos["cidade"].get(), campos["valor"].get())
        return ""

    def _gerar(self):
        try:
            data = self._obter_dados()
            if not data or all([len(v.get())==0 for v in self.campos_dyn.values()]):
                self._mostrar_msg("Preencha os campos obrigatórios!", error=True)
                return

            # Extrai “L”, “M”, “Q” ou “H” do texto selecionado
            ec_val = self.error_correction_var.get()
            if "(" in ec_val:
                ec_val = ec_val.split("(")[-1][0]
            else:
                ec_val = "H"

            self.qr_img_pil = gerar_qrcode(
                data,
                size=self.size_var.get(),
                fg_color=self.fg_color,
                bg_color=self.bg_color,
                border=self.border_var.get(),
                module_style=self.mod_style_var.get(),
                logo_path=self.logo_path,
                auto_resize_logo=self.auto_resize_logo.get(),
                error_correction=ec_val,
                box_size=self.box_size_var.get()
            )
            self._update_preview_img()
            self.save_btn.configure(state="normal")
            self.copy_btn.configure(state="normal")
            self._mostrar_msg("QR Code gerado com sucesso!", error=False)
        except Exception as e:
            self._mostrar_msg(f"Erro ao gerar QR: {e}", error=True)

    def _update_preview_img(self):
        if self.qr_img_pil is not None:
            size = self.size_var.get()
            img = self.qr_img_pil.resize((min(500, size), min(500, size)), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.preview_canvas.configure(image=tk_img)
            self.preview_canvas.image = tk_img

    def _salvar(self):
        if self.qr_img_pil is None:
            self._mostrar_msg("Gere um QR antes de salvar.", error=True)
            return

        ftypes = [("PNG", "*.png"), ("JPG", "*.jpg")]
        f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=ftypes)
        if not f: return

        try:
            self.qr_img_pil.save(f)
            self._mostrar_msg(f"QR Code salvo em {f}", error=False)
        except Exception as e:
            self._mostrar_msg(f"Erro ao salvar: {e}", error=True)

    def _copiar(self):
        try:
            import base64
            import pyperclip
            output = io.BytesIO()
            self.qr_img_pil.save(output, format="PNG")
            img_bytes = output.getvalue()
            b64data = base64.b64encode(img_bytes).decode()
            pyperclip.copy(b64data)
            self._mostrar_msg("QR (imagem) copiado em base64 para área de transferência!", error=False)
        except Exception:
            self._mostrar_msg("Requer pyperclip para copiar imagem em base64!", error=True)

    def _limpar(self):
        for v in self.campos_dyn.values():
            v.delete(0, "end")
        self.logo_path = None
        self.logo_preview.configure(text="(sem logo)")
        self.fg_color = "#FFFFFF"
        self.bg_color = "#000000"
        self.error_correction_var.set("Máxima (H)")
        self.box_size_var.set(10)
        self.size_var.set(400)
        self._update_color_previews()
        self._update_preview_img()
        self._mostrar_msg("Campos e cores resetados.", error=False)
        self._limpar_preview()

    def _limpar_preview(self):
        self.preview_canvas.configure(image="")
        self.preview_canvas.image = None
        self.qr_img_pil = None
        self.save_btn.configure(state="disabled")
        self.copy_btn.configure(state="disabled")

    def _mostrar_msg(self, txt, error=False):
        color = "#e53e3e" if error else "#10B981"
        self.msg_label.configure(text=txt, text_color=color)

if __name__ == "__main__":
    app = QRCodeApp()
    app.mainloop()

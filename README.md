# 🚀 OmniDesktop-MCP (Universal Desktop Application MCP Server)

**OmniDesktop-MCP** — bu lokal shaxsiy kompyuterda (Windows) o'rnatilgan ilovalarni (Blender 3D, Adobe After Effects, Photoshop, OBS Studio va barcha Windows dasturlarini) AI agentlar (**Claude Desktop**, **Cursor**, **Gemini**, **Antigravity**, **VS Code**) bilan bog'laydigan universal Model Context Protocol (MCP) serveri.

---

## 🌟 Imkoniyatlar (Key Features)

### 1. 🎨 Blender 3D Native Automation
- **Headless Python (`bpy`) Execution:** AI agent to'liq Python kodi orqali 3D modellar yasaydi, o'zgartiradi va `.blend` faylga saqlaydi.
- **EEVEE / Cycles Rendering:** 3D sahnalarni yuqori sifatli rasm (PNG/JPG) yoki ketma-ketlikda render qiladi.
- **3D Asset Export:** Sahnalarni `.glb`, `.gltf`, `.fbx`, `.obj` va `.stl` formatlariga avtomatik eksport qiladi.
- **Scene Introspection:** `.blend` fayli ichidagi obyektlar, materiallar, chiroqlar va kameralar ro'yxatini JSON ko'rinishida tahlil qiladi.
- **Procedural Studio Scene:** 3 nuqtali studiya yoritgichi, PBR materiallar va silliq geometriyali sahna yaratadi.

### 2. 🎬 Adobe After Effects & Motion Graphics
- **ExtendScript (.jsx) Execution:** After Effects'da dasturiy tarzda kompozitsiyalar, matnli qatlamlar va animatsiyalar yasaydi.
- **aerender CLI:** Loyihalarni fonda video faylga (MP4, MOV) render qiladi.
- **Title & Lower Third Generator:** Bir nechta parametr orqali tayyor animatsiyali sarlavhalar yaratadi.

### 3. 🖥️ Universal Windows GUI & Process Controller
- **App Detection & Launch:** Kompyuterdagi barcha dasturlarni qidirish, ro'yxatdan o'tkazish va fonda ochish.
- **Window Management:** Kerakli dastur oynasini sarlavhasi (title) bo'yicha topish va ekranning old planiga (foreground) chiqarish.
- **Visual Inspection (Screenshots):** Dastur oynasining yoki butun ekranning screenshotini olib, AI agentga taqdim etish.
- **Universal Input:** Klaviatura tugmalari (`Ctrl+S`, `Enter`, matn yozish) va sichqoncha koordinatalari orqali bosish.

### 4. ⚡ System & PowerShell Adapter
- **PowerShell Automation:** Windows PowerShell buyruqlarini xavfsiz bajarish.
- **System Diagnostics:** CPU, RAM, disk bo'sh joyi va operatsion tizim metrikalarini olish.

---

## 📁 Loyiha Strukturasi

```text
OmniDesktop-MCP/
├── core/
│   ├── discovery.py         # Windows registri va fayllardan ilovalarni qidiruvchi tizim
│   ├── executor.py          # Sinxron/asinxron jarayon va skript ijro etuvchisi
│   └── logger.py            # Strukturalangan jurnallash
├── adapters/
│   ├── base.py              # Har bir ilova adapteri uchun asosiy sinf
│   ├── blender_adapter.py   # Blender (bpy) bilan ishlash, render, eksport
│   ├── after_effects_adapter.py # After Effects (ExtendScript, aerender)
│   ├── universal_gui_adapter.py # Windows oynalari, screenshot, input
│   └── system_adapter.py    # PowerShell va tizim ma'lumotlari
├── templates/
│   ├── blender_templates.py # Procedural PBR va studiya shablonlari
│   └── ae_templates.py      # Lower-third va matn animatsiyasi shablonlari
├── tests/
│   ├── test_discovery.py    # Qidiruv va tizim testlari
│   └── test_adapters.py     # Adapterlar va xatoliklar testlari
├── install.bat              # Windows uchun 1-klikda to'liq o'rnatish
├── run.bat                  # Serverni ishga tushirish skripti
├── setup_agent.py           # Claude Desktop va Cursor uchun avtomatik konfigurator
├── cli.py                   # Konsolda diagnostika va tezkor tekshirish vositasi
├── requirements.txt         # Kerakli Python kutubxonalari
└── server.py                # Asosiy FastMCP serveri
```

---

## 🚀 O'rnatish va Ishga Tushirish

### 1-usul: Bir klikda avtomatik o'rnatish (Tavsiya etiladi)

Loyihani ko'chirib olgandan so'ng, shunchaki:
```cmd
install.bat
```
faylini ikki marta bosing. U avtomatik:
1. `venv` (virtual muhit) yaratadi.
2. Barcha kerakli kutubxonalarni o'rnatadi.
3. Kompyuteringizdagi **Claude Desktop** sozlamalariga (`claude_desktop_config.json`) serverni ulaydi.

### 2-usul: Qo'lda o'rnatish (Manual Setup)

```powershell
cd C:\Users\user\OmniDesktop-MCP
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python setup_agent.py
```

---

## 🤖 AI Agentlarga ulash (Configuration)

### Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "omnidesktop": {
      "command": "C:/Users/user/OmniDesktop-MCP/venv/Scripts/python.exe",
      "args": ["C:/Users/user/OmniDesktop-MCP/server.py"]
    }
  }
}
```

### Cursor / VS Code / Boshqa MCP mijozlar
Buyruq: `C:/Users/user/OmniDesktop-MCP/venv/Scripts/python.exe`
Argumentlar: `["C:/Users/user/OmniDesktop-MCP/server.py"]`

---

## 🛠️ Mavjud Tool'lar (MCP Tools Reference)

| Tool | Tavsifi |
|---|---|
| `get_installed_apps` | Kompyuterda o'rnatilgan Blender, AE, Photoshop, OBS va yo'llarini aniqlaydi |
| `search_installed_software` | Windows registridan istalgan dasturni nomi bo'yicha qidiradi |
| `system_get_specs` | CPU, RAM, disk va OS ko'rsatkichlarini qaytaradi |
| `system_run_powershell` | PowerShell buyrug'ini bajaradi |
| `blender_run_python` | Blender ichida Python (`bpy`) kodini bajaradi va `.blend` faylga saqlaydi |
| `blender_render_frame` | 3D sahnani rasmga (PNG/JPG) render qiladi (EEVEE/Cycles) |
| `blender_export_3d_asset` | Sahnani GLB, GLTF, FBX, OBJ yoki STL formatiga eksport qiladi |
| `blender_get_scene_info` | `.blend` faylidagi barcha obyektlar, materiallar va kameralarni ko'rsatadi |
| `blender_create_studio_scene` | Tayyor 3D studiya sahnasini procedural yaratadi |
| `ae_run_extendscript` | After Effects'da `.jsx` ExtendScript skriptini yurgizadi |
| `ae_render_composition` | `aerender.exe` orqali After Effects kompozitsiyasini video qiladi |
| `ae_create_title_animation` | After Effects'da animatsiyali sarlavha yaratadi |
| `desktop_list_windows` | Ochiq dasturlar oynalarini (title, PID, RAM) ro'yxatini ko'rsatadi |
| `desktop_launch_app` | Istalgan Windows dasturini ishga tushiradi |
| `desktop_focus_window` | Dastur oynasini ekranning oldiga chiqaradi |
| `desktop_take_screenshot` | Oyna yoki butun ekranning PNG screenshotini oladi |
| `desktop_send_keys` | Tugmalarni bosadi yoki matn kiritadi (`Ctrl+S`, `Enter` va h.k.) |
| `desktop_click_mouse` | Sichqonchani belgilangan koordinataga bosadi |

---

## 🧪 Sinov va Testlash (Testing)

Terminal orqali server imkoniyatlarini tekshirish uchun qulay `cli.py` mavjud:
```powershell
# Ilovalarni aniqlashni tekshirish
.\venv\Scripts\python cli.py discover

# Ochiq dasturlar oynalarini ko'rish
.\venv\Scripts\python cli.py windows

# Tizim xarakteristikalarini ko'rish
.\venv\Scripts\python cli.py specs

# Blenderda 3D kub yaratish va saqlashni tekshirish
.\venv\Scripts\python cli.py blender-test --save my_cube.blend

# Screenshot olish
.\venv\Scripts\python cli.py screenshot --output desktop_snap.png
```

To'liq avtomatlashtirilgan testlarni ishga tushirish:
```powershell
.\venv\Scripts\python -m pytest tests -v
```

import os

import requests
import streamlit as st

# Endereço da API. Em produção: https://sistema-de-wishlist.onrender.com
API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Wishlist de Jogos", page_icon="🎮")


# ---------- Comunicação com a API ----------
def http() -> requests.Session:
    # Uma sessão HTTP por usuário do Streamlit: ela guarda o cookie de login da API
    if "http" not in st.session_state:
        st.session_state.http = requests.Session()
    return st.session_state.http


def call(method: str, path: str, **kwargs):
    try:
        response = http().request(method, f"{API_URL}{path}", timeout=90, **kwargs)
    except requests.RequestException:
        st.error("Não foi possível falar com a API. No Render ela pode levar até 1 minuto para acordar.")
        st.stop()
    if response.status_code == 401 and st.session_state.get("user"):
        logout_local("Sua sessão expirou. Entre novamente.")
    return response


def error_message(response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        return f"Erro {response.status_code}"
    if isinstance(detail, list):  # erros de validação (422)
        return "; ".join(item.get("msg", "") for item in detail)
    return detail or f"Erro {response.status_code}"


def logout_local(message: str | None = None):
    for key in ("http", "user", "pending"):
        st.session_state.pop(key, None)
    if message:
        st.session_state.flash = message
    st.rerun()


# ---------- Telas sem login ----------
def login_screen():
    st.title("🎮 Wishlist de Jogos")
    if st.session_state.get("flash"):
        st.info(st.session_state.pop("flash"))

    if st.session_state.get("pending"):
        code_screen()
        return

    tab_login, tab_signup = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                response = call("POST", "/auth/login", json={"email": email, "password": password})
                if response.ok:
                    st.session_state.pending = response.json()["message"]
                    st.rerun()
                st.error(error_message(response))

    with tab_signup:
        with st.form("signup"):
            username = st.text_input("Nome")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Senha", type="password", key="signup_password")
            phone = st.text_input("Celular", placeholder="+5585999999999")
            if st.form_submit_button("Criar conta"):
                response = call(
                    "POST",
                    "/users",
                    json={"username": username, "email": email, "password": password, "phone": phone},
                )
                if response.ok:
                    st.success("Conta criada. Agora entre pela aba ao lado.")
                else:
                    st.error(error_message(response))


def code_screen():
    st.success(st.session_state.pending)
    with st.form("verify"):
        code = st.text_input("Código de 6 dígitos recebido por SMS", max_chars=6)
        if st.form_submit_button("Confirmar", type="primary"):
            response = call("POST", "/auth/verify", json={"code": code.strip()})
            if response.ok:
                st.session_state.pop("pending")
                st.session_state.user = call("GET", "/auth/me").json()
                st.rerun()
            st.error(error_message(response))
    if st.button("Voltar"):
        logout_local()


# ---------- Telas com login ----------
def load_games() -> list[dict]:
    response = call("GET", "/games")
    return response.json() if response.ok else []


def game_label(game: dict) -> str:
    extras = " · ".join(v for v in (game.get("genre"), game.get("platform")) if v)
    return f"{game['title']} ({extras})" if extras else game["title"]


def catalog_page():
    st.header("Catálogo de jogos")
    games = load_games()
    if not games:
        st.info("Nenhum jogo cadastrado ainda.")
        return
    st.dataframe(
        [{"Jogo": g["title"], "Gênero": g.get("genre"), "Plataforma": g.get("platform"),
          "Lançamento": g.get("release_date") or "-"} for g in games],
        hide_index=True,
        width="stretch",
    )

    if st.session_state.user["role"] == "user":
        options = {game_label(g): g["id"] for g in games}
        choice = st.selectbox("Adicionar à minha wishlist", options)
        if st.button("Adicionar", type="primary"):
            response = call("POST", "/wishlist", json={"game_id": options[choice]})
            if response.ok:
                st.success("Jogo adicionado à wishlist.")
            else:
                st.error(error_message(response))


def wishlist_page():
    st.header("Minha wishlist")
    items = call("GET", "/wishlist").json()
    games = {g["id"]: g for g in load_games()}
    if not items:
        st.info("Sua wishlist está vazia. Adicione jogos pelo catálogo.")
        return
    for item in items:
        game = games.get(item["game_id"], {"title": f"Jogo #{item['game_id']}"})
        col_name, col_button = st.columns([4, 1])
        col_name.write(f"**{game_label(game)}** — adicionado em {item.get('created_at') or '-'}")
        if col_button.button("Remover", key=f"remove-{item['id']}"):
            response = call("DELETE", f"/wishlist/{item['id']}")
            if response.ok:
                st.rerun()
            st.error(error_message(response))


def manage_games_page():
    st.header("Gerenciar jogos")

    with st.expander("Adicionar jogo", expanded=True):
        with st.form("new_game", clear_on_submit=True):
            title = st.text_input("Título")
            genre = st.text_input("Gênero")
            platform = st.text_input("Plataforma")
            release = st.date_input("Lançamento", value=None, format="DD/MM/YYYY")
            if st.form_submit_button("Adicionar", type="primary"):
                payload = {"title": title, "genre": genre or None, "platform": platform or None,
                           "release_date": release.isoformat() if release else None}
                response = call("POST", "/games", json=payload)
                if response.ok:
                    st.success(f"\"{title}\" adicionado ao catálogo.")
                else:
                    st.error(error_message(response))

    games = load_games()
    if not games:
        return
    with st.expander("Editar ou remover jogo"):
        options = {game_label(g): g for g in games}
        game = options[st.selectbox("Jogo", options)]
        with st.form(f"edit_game_{game['id']}"):
            title = st.text_input("Título", game["title"])
            genre = st.text_input("Gênero", game.get("genre") or "")
            platform = st.text_input("Plataforma", game.get("platform") or "")
            col_save, col_delete = st.columns(2)
            save = col_save.form_submit_button("Salvar alterações", type="primary")
            delete = col_delete.form_submit_button("Remover do catálogo")
        if save:
            response = call("PUT", f"/games/{game['id']}",
                            json={"title": title, "genre": genre or None, "platform": platform or None})
            if response.ok:
                st.rerun()
            st.error(error_message(response))
        if delete:
            response = call("DELETE", f"/games/{game['id']}")
            if response.ok:
                st.rerun()
            st.error(error_message(response))


def users_page():
    st.header("Usuários")
    response = call("GET", "/users")
    if not response.ok:
        st.error(error_message(response))
        return
    users = response.json()
    st.dataframe(
        [{"Id": u["id"], "Nome": u["username"], "Email": u["email"], "Papel": u["role"]} for u in users],
        hide_index=True,
        width="stretch",
    )

    others = {f"{u['username']} ({u['email']})": u for u in users if u["id"] != st.session_state.user["id"]}
    if not others:
        return
    st.subheader("Alterar papel")
    target = others[st.selectbox("Usuário", others)]
    role = st.radio("Papel", ["user", "admin"], index=["user", "admin"].index(target["role"]), horizontal=True)
    if st.button("Salvar papel", type="primary"):
        response = call("PATCH", f"/users/{target['id']}/role", json={"role": role})
        if response.ok:
            st.rerun()
        st.error(error_message(response))


# ---------- Aplicação ----------
def main():
    user = st.session_state.get("user")
    if not user:
        login_screen()
        return

    is_admin = user["role"] == "admin"
    with st.sidebar:
        st.write(f"Olá, **{user['username']}**")
        st.caption("Administrador" if is_admin else "Usuário")
        pages = ["Catálogo", "Gerenciar jogos", "Usuários"] if is_admin else ["Catálogo", "Minha wishlist"]
        page = st.radio("Menu", pages, label_visibility="collapsed")
        if st.button("Sair"):
            call("POST", "/auth/logout")
            logout_local("Você saiu da sua conta.")

    {
        "Catálogo": catalog_page,
        "Minha wishlist": wishlist_page,
        "Gerenciar jogos": manage_games_page,
        "Usuários": users_page,
    }[page]()


main()

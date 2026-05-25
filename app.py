import json
import uuid
from datetime import datetime, date, time, timezone, timedelta
from pathlib import Path

import streamlit as st
from streamlit_sortables import sort_items

SWEDISH_TZ = timezone(timedelta(hours=2))

DATA_FILE = Path(__file__).parent / "polls.json"


def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {}


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def create_poll():
    st.header("Skapa en omröstning")

    question = st.text_input("Fråga")

    if "num_options" not in st.session_state:
        st.session_state.num_options = 2

    options = []
    for i in range(st.session_state.num_options):
        opt = st.text_input(f"Alternativ {i + 1}", key=f"opt_{i}")
        options.append(opt)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Lägg till alternativ"):
            st.session_state.num_options += 1
            st.rerun()
    with col2:
        if st.session_state.num_options > 2 and st.button("- Ta bort sista"):
            st.session_state.num_options -= 1
            st.rerun()

    st.subheader("När ska resultatet visas?")
    reveal_date = st.date_input("Datum", value=date.today())
    reveal_time = st.time_input("Tid", value=time(15, 0), step=timedelta(minutes=1))

    if st.button("Skapa omröstning"):
        options = [o.strip() for o in options if o.strip()]
        if not question.strip():
            st.error("Skriv en fråga.")
            return
        if len(options) < 2:
            st.error("Lägg till minst 2 alternativ.")
            return

        poll_id = uuid.uuid4().hex[:6]
        reveal_at = datetime.combine(reveal_date, reveal_time).isoformat()

        data = load_data()
        data[poll_id] = {
            "question": question.strip(),
            "options": options,
            "scores": {opt: 0 for opt in options},
            "num_responses": 0,
            "reveal_at": reveal_at,
        }
        save_data(data)

        st.success("Omröstningen är skapad!")
        st.info("Dela denna länk:")
        st.code(f"?poll={poll_id}")


def show_poll(poll_id):
    data = load_data()

    if poll_id not in data:
        st.error("Omröstningen finns inte.")
        return

    poll = data[poll_id]
    now = datetime.now(SWEDISH_TZ).replace(tzinfo=None)
    reveal_at = datetime.fromisoformat(poll["reveal_at"])

    st.header(poll["question"])

    if now >= reveal_at:
        st.subheader("Resultat")
        scores = poll["scores"]
        num = poll.get("num_responses", 0)
        top3 = sorted(poll["options"], key=lambda o: scores[o], reverse=True)[:3]
        medals = ["🥇", "🥈", "🥉"]
        max_score = scores[top3[0]] if top3 else 1
        for i, option in enumerate(top3):
            pts = scores[option]
            st.write(f"## {medals[i]} {option}")
            st.write(f"{pts} poäng")
            st.progress(pts / max_score if max_score > 0 else 0)
    else:
        voted_key = f"voted_{poll_id}"

        if st.session_state.get(voted_key):
            st.success(
                f"Tack! Resultatet visas {reveal_at.strftime('%Y-%m-%d')} kl {reveal_at.strftime('%H:%M')}."
            )
            return

        n = len(poll["options"])
        st.write("Dra och släpp för att rangordna (överst = bäst):")
        sorted_order = sort_items(poll["options"], direction="vertical")

        if st.button("Skicka"):
            data = load_data()
            for i, option in enumerate(sorted_order):
                data[poll_id]["scores"][option] += (n - i)
            data[poll_id]["num_responses"] = data[poll_id].get("num_responses", 0) + 1
            save_data(data)
            st.session_state[voted_key] = True
            st.rerun()


def main():
    st.set_page_config(page_title="Omröstning", page_icon="🗳️")
    st.title("🗳️ Omröstning")

    params = st.query_params
    poll_id = params.get("poll")

    if poll_id:
        show_poll(poll_id)
    else:
        create_poll()


main()

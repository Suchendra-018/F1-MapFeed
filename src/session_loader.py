import fastf1

fastf1.Cache.enable_cache("data")


def load_session(year, race, session_type):
    session = fastf1.get_session(
        year,
        race,
        session_type
    )

    session.load()

    return session
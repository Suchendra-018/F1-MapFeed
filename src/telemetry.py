def get_fastest_lap_telemetry(session, driver_code):

    driver_laps = session.laps.pick_drivers(driver_code)

    fastest_lap = driver_laps.pick_fastest()

    telemetry = fastest_lap.get_car_data().add_distance()

    return telemetry

def get_fastest_lap(session, driver_code):

    driver_laps = session.laps.pick_drivers(
        driver_code
    )

    return driver_laps.pick_fastest()
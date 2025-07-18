import asyncio
from pprint import pprint

from czfb_server.tools.transport.services.departure_service import get_departures, departures_by_coordinates
from czfb_server.tools.transport.services.geocoding_service import geocode
from czfb_server.tools.transport.services.stop_service import reverse_geocode, list_all_stops, get_stop_metadata, \
    find_all_stops_near
from czfb_server.tools.transport.services.trip_service import plan_trip_between


async def test_geocode():
    print("🔍 Geocoding 'Anděl'...")
    result = await geocode("Anděl")
    pprint(result)


async def test_plan_trip():
    print("\n🧭 Planning trip from 'Anděl' to 'Karlovo náměstí'...")
    result = await plan_trip_between("Anděl", "Karlovo náměstí", "in 20 minutes")
    pprint(result)


async def test_get_departures():
    print("\n🚌 Departures from 'Hlavní nádraží'...")
    result = await get_departures("Hlavní nádraží", "in 15 minutes")
    pprint(result)


async def test_departures_by_coords():
    print("\n📍 Departures by coordinates near Anděl...")
    result = await departures_by_coordinates(50.0709, 14.4039)
    pprint(result)


async def test_reverse_geocode():
    print("\n📍 Reverse geocode near Karlovo náměstí...")
    result = await reverse_geocode(50.0758, 14.4184)
    pprint(result)


async def test_list_all_stops():
    print("\n📋 Listing all stops containing 'Florenc'...")
    result = await list_all_stops(name_contains="Florenc")
    pprint(result)


async def test_stop_metadata():
    print("\n📋 Getting stop metadata for 'Florenc'...")
    result = await get_stop_metadata(stop_name="Florenc")
    pprint(result)


async def test_nearby_stops():
    print("\n📡 Finding all stops within 300m of Náměstí Míru...")
    result = await find_all_stops_near(50.0757, 14.4378, radius=300)
    pprint(result)


if __name__ == "__main__":
    asyncio.run(test_geocode())
    asyncio.run(test_plan_trip())
    asyncio.run(test_get_departures())
    asyncio.run(test_departures_by_coords())
    asyncio.run(test_reverse_geocode())
    asyncio.run(test_list_all_stops())
    asyncio.run(test_stop_metadata())
    asyncio.run(test_nearby_stops())

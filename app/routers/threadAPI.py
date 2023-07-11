import asyncio
from fastapi import APIRouter
from starlette.background import BackgroundTasks
from threads import Threads

follow_list = {54604060272: True, 3319230929: True, 6410227468: True, 53612758148: True, 1695101239: True, 60962720683: True, 60616348733: True, 2911140: True, 57388446982: True, 57232750451: True, 1647560998: True, 60778266469: True, 533172144: True, 51638206737: True, 1560866010: True, 55937430257: True, 46657731698: True, 19833810705: True, 1965132438: True, 1545643276: True, 48767054: True, 60807041590: True, 1713613300: True, 52580293035: True, 3721303539: True, 34677434966: True, 1789191148: True, 664225517: True, 58739801213: True, 1593117225: True, 1447639785: True, 11061574232: True, 1396816848: True, 60595774957: True, 1396491161: True, 2941799615: True, 44912715162: True, 2895876697: True, 13382020026: True, 1702649830: True, 7348376542: True, 15750085625: True, 8422558306: True, 4905748209: True, 4973752663: True, 7178813807: True, 1489051348: True, 2887317909: True, 5744440457: True, 34667198773: True, 12985404286: True, 2036131895: True, 59320425111: True, 5948997971: True, 1736517311: True, 6084558892: True, 27491304741: True, 10466847643: True, 2041516256: True, 3975646774: True, 1060674837: True, 1939087330: True, 50725195853: True, 48665905338: True, 29636038451: True, 6845798531: True, 1186580686: True, 18296221953: True, 52638341873: True, 3665491837: True, 57013488008: True, 60419962653: True, 47185093568: True, 45944311574: True, 6958477767: True, 53171894939: True, 51952611350: True, 30562075488: True, 22373509975: True, 6631603167: True, 40227560772: True, 45602210492: True, 3120782172: True, 1820498229: True, 44680439756: True, 4361721511: True, 31925488881: True, 8679407103: True, 2125755836: True, 56900527279: True, 54153925327: True, 1523073441: True, 1274374524: True, 60786507167: True, 789875: True, 1379921559: True}

router = APIRouter(prefix="/thread")

@router.get("/")
def read_root(background_tasks: BackgroundTasks):
    background_tasks.add_task(follow_back)
    return {"message": "Follow Back Bot is running."}
async def follow_back():
    # Get the list of followers
    while True:
        threads = Threads(username='_vast1y_', password='twcho0205@')
        my_id = int(threads.private_api.get_user_id('_vast1y_'))
        followers = threads.private_api.get_user_followers(id=int(my_id))
        print(f"Checking {len(followers['users'])} followers...")

        new_follows = 0
        # For each follower, check if you are following them
        for follower in followers['users']:
            # Get the user's followings
            # new_id = threads.private_api.get_user_id(follower['pk'])
            if follower['pk'] in follow_list:
                continue
            follow_list[follower['pk']] = True
            response = threads.private_api.follow_user(id=int(follower['pk']))
            if response['status'] == 'ok':
                new_follows += 1
                print(f"Successfully followed {follower['username']}")
            else:
                print(f"Failed to follow {follower['username']}. Response: {response}")


        print(f"Followed {new_follows} new users this round.")
        await asyncio.sleep(600)
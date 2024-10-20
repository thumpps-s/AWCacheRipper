from pathlib import Path
from itertools import chain
import steam.monkey
steam.monkey.patch_minimal()

from steam.client import SteamClient
from steam.webauth import WebAuth
from steam.client.cdn import CDNClient
from steam.enums.emsg import EMsg
from steam.enums.common import EResult

# setup some constants
MAX_ATTEMPTS = 5
AMAZING_WORLD_APP_ID = 293500
DOWNLOAD_PATH = Path(".") / "ripped_cache"
# steam won't give us historic manifests through the api,
# so we're reliant on manually grabbing them from steamdb
DEPOT_MANIFESTS = {
        293501: [
            6317617349025604005,
            7901909182090048109,
            8758222581888309958,
            9110856610459770731,
            7361989920334497104,
            2080539683849689559,
            7522369262151290680,
            8663629755761522634,
            6502095650937049075,
            150062268824784829,
            8015868864262836906,
            6706989371693610108,
            1100904527554409606,
            5866416088790772011,
            1163628279238678070,
            3138486940304030216,
            7534742988546406459,
            5051060530706354264,
            5548964149751274327,
            3277879104470999868,
            2693875605870651590,
            3657230167584882315,
            9117308655041946429,
            8284429884913417926,
            1382819626877884623,
            5544770557117312106,
            8919686501475467957,
            1223679262185020730,
            7321267361052596787,
            7846889394918211010,
            2356502868104161957,
            4824038850308821259,
            3714932279606775655,
            2654417047934109613,
            4238132967940279645,
            6248933968866779609,
            4869693191109066594,
            5571235727418202569,
            5593323304350088511,
            7403576822807954865,
            8494177947226436877,
            4418700564363249443,
            2248126420478329762,
            4346240986834231971,
            9131653841140571725,
            4801916126462387377,
            6729884438886554881,
            696889255134693781,
            8401626197987041336,
            8993828910270140717,
            1382147567957797041,
            3311710529355782156,
            363590375114713954,
            1400067595504782317,
            2789397579935834104,
            5666130179501948897,
            3614500876694365785,
            6211026949820130274,
            3072836546280820460,
            4934647830286672300,
            5937200490702340812,
            2256268439874368179,
            2848842034847978740,
            339696732245605885,
            679972422337816081,
            3677212900165390589,
            7685656323934911892,
            2187642615820242225
        ],
        293502: [
            6976046015200551653,
            7434659534656466939,
            4593363053893958384,
            1855988643759491044,
            417675091598665939,
            5048556284593049514,
            64272713095478299,
            742293010074751113,
            1768233694191980156,
            5702970702078503775,
            1863561368871191806,
            161333089303444168,
            6804395299688003806,
            2740198665555706190,
            4835081623195306379,
            2881732420148939804,
            8680626583365308545,
            8211539774131770072,
            1226756472519781729,
            8657953874361494418,
            7217065568365630284,
            572526046190622298,
            7878062350946071682,
            9183633153345533779,
            6953697232577526526,
            5687345293703687745,
            2795001042030249200,
            3013390925226098061,
            2029403427308937464,
            8965711142630886406,
            1558873975543412592,
            1495827120273904283,
            5032226823591410369,
            5142494565528199982,
            3946258836179997164,
            1122789140424907849,
            2404860352876401933,
            8926192903925306937,
            7476132708547691062,
            6458461401224533488,
            8135498943259023603,
            7595069956374928861,
            8758727242172112567,
            9097677258358811142,
            8969903473878274384,
            4464121216402897255,
            8677847584926301129,
            9134872048153908613,
            6640032166567628692,
            2769152859585958934,
            239453404116901217,
            6710398270162904682,
            4434373945281349367,
            7480384856702011949,
            5280268903602080096,
            2385618127000341243,
            7029840289471228821,
            2468697631891846734,
            3748408866069318015,
            4261751048980822951,
            1053497082692979046,
            277829877071766055,
            350172155206269773,
            7630599910101563346,
            5354494244187143610,
            8711532276816726582,
            2852803683067694270,
            8273423153640530686,
            8366332084153946304
        ]
}

# get credentials
webauth = WebAuth()
username = input("steam username: ")
_ = webauth.cli_login(username)

# get client using hack for current steam issues
# https://github.com/ValvePython/steam/issues/474
client = SteamClient()
from steam import webapi
try:
    resp = webapi.get('ISteamDirectory', 'GetCMListForConnect', 1, params={'cmtype': 'netfilter',
                                                                 'http_timeout': 3})
except Exception as exp:
    client.cm_servers._LOG.error("WebAPI boostrap failed: %s" % str(exp))

result = EResult(resp['response']['success'])

if result != EResult.OK:
    client.cm_servers._LOG.error("GetCMList failed with %s" % repr(result))

serverlist = resp['response']['serverlist']
client.cm_servers._LOG.debug("Received %d servers from WebAPI" % len(serverlist))

def str_to_tuple(serveraddr):
    ip, port = serveraddr['endpoint'].split(':')
    return str(ip), int(port)

client.cm_servers.clear()
client.cm_servers.merge_list(map(str_to_tuple, serverlist))

# login
client.login(webauth.username, access_token=webauth.refresh_token)
cdn = CDNClient(client)
print("login successful, retrieving manifests...")

# get all manifests
manifests = []
for depot, manifest_gids in DEPOT_MANIFESTS.items():
    for manifest_gid in manifest_gids:
        request_code = cdn.get_manifest_request_code(
            AMAZING_WORLD_APP_ID,
            depot,
            manifest_gid
        )
        manifest = cdn.get_manifest(
            AMAZING_WORLD_APP_ID,
            depot,
            manifest_gid,
            manifest_request_code=request_code
        )
        manifests.append(manifest)
        print(f"retrieved depot:manifest {depot}:{manifest_gid}")

# create iterator across all cache files
print("creating iterator across all cache files...")
cache_file_iters = [manifest.iter_files(pattern="Cache/*") for manifest in manifests]
cache_files = chain(*cache_file_iters)
print("done, retrieving...")

# get all files
known_hashes = set()
known_names = set()
failed_downloads = list()
for file in cache_files:

    # dedupe files, whilst still downloading files with unique names
    sha = file.sha_content
    filename = file.filename
    if sha in known_hashes and filename in known_names:
        continue
    if filename in known_names:
        filename += f"-{sha}"
    known_hashes.add(sha)
    known_names.add(file.filename)

    # download files
    out_path = DOWNLOAD_PATH / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading unique hash #{len(known_hashes)} to {out_path}...")
    for attempt in range(MAX_ATTEMPTS - 1):
        try:
            content = file.read()
            with open(out_path, "wb") as local_file:
                local_file.write(file.read())
            break
        except Exception as e:
            if attempt == MAX_ATTEMPTS - 1:
                print(f"failed to download file {out_path}: {e}")
                failed_downloads.append((out_path, e))
            else:
                print("download problem, retrying...")


print(f"done. check {DOWNLOAD_PATH} for output")
if failed_downloads:
    print("failed downloads:")
    for file, exception in failed_downloads:
        print(f"{file}: {exception}")

# logout and quit
client.logout()
import requests
import json
from utils import common

class RPC:
    version = "2.0"
    id = 0

    url="http://127.0.0.1:8820/rpc/v2"

    def __init__(self, method):
        self.method = method
        self.__class__.id += 1
        self.id = self.__class__.id

    def __to_data(self, positional, optional):
        optional_params = []
        for key in optional:
            value = optional[key]
            if type(value) in (tuple, list):
                for v in value:
                    optional_params.append(key)
                    optional_params.append(v)
            elif value == None:
                continue
            else:
                optional_params.append(key)
                optional_params.append(value)

        ret = {
            'method' : self.method,
            'id' : self.id,
            'jsonrpc' : self.version,
            "params": positional + optional_params}
        return json.dumps( ret )

    def post(self, positional, optional):
        rpc_rsp = requests.post(self.url, data=self.__to_data(positional, optional))
        assert (rpc_rsp.json()['id'] == self.id)
        return rpc_rsp

def mvs_api(func):
    def wrapper(*args, **kwargs):
        cmd, positional, optional, result_handler = func(*args, **kwargs)
        rpc_cmd = RPC(cmd)
        rpc_rsp = rpc_cmd.post(positional, optional)
        if "error" in rpc_rsp.json():
            print(rpc_rsp.json()['error']['code'], rpc_rsp.json()['error']['message'])
            return rpc_rsp.json()['error']['code'], rpc_rsp.json()['error']['message']
        if result_handler:
            return 0, result_handler(rpc_rsp.json()['result'])
        return 0, rpc_rsp.json()['result']
    return wrapper

def mvs_api_v3(func):
    def wrapper(*args, **kwargs):
        cmd, positional, optional, result_handler = func(*args, **kwargs)
        rpc_cmd = RPC(cmd)
        rpc_cmd.url = RPC.url.replace('/v2', '/v3')
        rpc_rsp = rpc_cmd.post(positional, optional)
        if "error" in rpc_rsp.json():
            return rpc_rsp.json()['error']['code'], rpc_rsp.json()['error']['message']
        if result_handler:
            return 0, result_handler(rpc_rsp.json()['result'])
        return 0, rpc_rsp.json()['result']
    return wrapper

@mvs_api
def getpeerinfo():
    '''
    {
        "peers" :  <-- return
        [
            "10.10.10.184:52644"
        ]
    }
    '''
    return "getpeerinfo", [], {}, lambda result: result["peers"]

@mvs_api
def getblockheader(hash=None, height=None):
    return "getblockheader", [], {"-s":hash, "-t":height}, lambda result: (result['hash'], result['number'])

@mvs_api
def dump_keyfile(account, password, lastword, keyfile=""):
    return "dumpkeyfile", [account, password, lastword, keyfile], {}, None

@mvs_api
def import_keyfile(account, password, keystore_file, keyfile_content=None):
    if keyfile_content:
        args = [account, password, "omitted", keyfile_content]
    else:
        args = [account, password, keystore_file]
    return "importkeyfile", args, {}, None

@mvs_api
def new_account(account, password):
    return "getnewaccount", [account, password], {}, lambda result: result["mnemonic"].split()

@mvs_api
def get_account(account, password, lastword):
    return "getaccount", [account, password, lastword], {}, lambda result: (result["mnemonic-key"], result["address-count"])

@mvs_api
def new_address(account, password, address_count=1):
    return "getnewaddress", [account, password], {'--number' : address_count}, lambda result: result["addresses"]

@mvs_api
def list_addresses(account, password):
    return "listaddresses", [account, password], {}, lambda result: result["addresses"]

@mvs_api
def check_address(address):
    return "validateaddress", [address], {}, None

@mvs_api
def delete_account(account, password, lastword):
    return "deleteaccount", [account, password, lastword], {}, None

@mvs_api
def import_account(account, password, mnemonic, hd_index=None):
    return "importaccount", [mnemonic], {
        '--accountname' : account,
        '--password' : password,
        '--hd_index' : hd_index
    }, None

@mvs_api
def change_passwd(account, password, new_password):
    return "changepasswd", [account, password], {'--password':new_password}, None

@mvs_api
def get_publickey(account, password, address):
    return "getpublickey", [account, password, address], {}, lambda result: result["public-key"]

@mvs_api
def getnew_multisig(account, password, description, my_publickey, others_publickeys, required_key_num):
    assert(my_publickey not in others_publickeys)
    n = len(others_publickeys) + 1
    m = required_key_num

    return "getnewmultisig", \
           [account, password], \
           {
            '-d': description,
            '-s': my_publickey,
            '-k': others_publickeys,
            '-m' : m,
            '-n' : n
           }, \
           None

@mvs_api
def list_multisig(account, password):
    return "listmultisig", [account, password], {}, None

@mvs_api
def delete_multisig(account, password, addr):
    return "deletemultisig", [account, password, addr], {}, None

@mvs_api
def create_multisigtx(account, password, from_, to_, amount):
    '''
    ACCOUNTNAME          Account name required.
    ACCOUNTAUTH          Account password(authorization) required.
    FROMADDRESS          Send from this address
    TOADDRESS            Send to this address
    AMOUNT               ETP integer bits.
    '''
    return "createmultisigtx", [account, password, from_, to_, amount], {}, None

@mvs_api
def sign_multisigtx(account, password, tx, broadcast=False):
    '''
    ACCOUNTNAME          Account name required.
    ACCOUNTAUTH          Account password(authorization) required.
    TRANSACTION          The input Base16 transaction to sign.
    -b [--broadcast]     Broadcast the tx if it is fullly signed.
    '''
    positional = [account, password, tx]
    if broadcast:
        positional.append('-b')
    return "signmultisigtx", positional, {}, None

@mvs_api
def get_balance(account, password):
    '''Show total balance details of this account.'''
    return 'getbalance', [account, password], {}, None

@mvs_api
def list_balances(account, password, range_):
    '''
    :param range_: (from, to)
    '''
    return "listbalances", [account, password], {
        '-g' : range_[0],
        '-l' : range_[1]
    }, None

@mvs_api
def issue_did(account, password, address, did_symbol, fee=None):
    return "issuedid", [account, password, address, did_symbol], {'--fee' : fee}, None

@mvs_api
def list_dids(account=None, password=None):
    return "listdids", [account, password], {}, None

@mvs_api
def modify_did(account, password, to_address, did_symbol):
    return "didmodifyaddress", [account, password, to_address, did_symbol], {}, None

@mvs_api
def list_didaddresses(account, password, did_symbol):
    return "listdidaddresses", [account, password, did_symbol], {}, None

@mvs_api
def get_asset(asset_symbol=None, cert=False):
    positional = filter(None, [asset_symbol])
    if cert:
        positional.append("--cert")
    return "getasset", positional, {}, None

@mvs_api
def get_addressasset(address, cert=False):
    args = [address]
    if cert:
        args.append('--cert')
    return "getaddressasset", args, {}, None

@mvs_api
def get_accountasset(account, password, asset_symbol=None, cert=False):
    args = [account, password, asset_symbol]
    if cert:
        args.append('--cert')
    return "getaccountasset", filter(None, args), {}, None

@mvs_api
def create_asset(account, password, symbol, volume, issuer, description=None, decimalnumber=None, rate=None):
    optionals = {
        '--symbol' : symbol,
        '--volume': volume,
        '--description': description,
        '--issuer': issuer,
        '--decimalnumber': decimalnumber,
        '--rate': rate
    }

    return "createasset", [account, password], optionals, None

@mvs_api
def delete_localasset(account, password, symbol):
    return "deletelocalasset", [account, password], {'--symbol' : symbol}, None

@mvs_api
def issue_asset(account, password, symbol, fee=None, model=None):
    return "issue", [account, password, symbol], {"--fee":fee, "--model":model}, None

@mvs_api
def issue_asset_from(account, password, symbol, from_):
    return "issuefrom", [account, password, from_, symbol], {}, None

@mvs_api
def delete_localasset(account, password, symbol):
    return "deletelocalasset", [account, password], {'--symbol': symbol}, None

@mvs_api
def list_assets(account=None, password=None, cert=False):
    positional = filter(None, [account, password])
    if cert:
        positional.append('--cert')
    return "listassets", positional, {}, None

@mvs_api
def send_asset(account, password, to_, symbol, amount, fee=None):
    return "sendasset", [account, password, to_, symbol, amount], {'--fee': fee}, None

@mvs_api
def send_asset_from(account, password, from_, to_, symbol, amount, fee=None):
    return "sendassetfrom", [account, password, from_, to_, symbol, amount], {'--fee': fee}, None

@mvs_api
def set_miningaccount(account, password, address):
    return "setminingaccount", [account, password, address], {}, None

@mvs_api
def start_mining(account, password, address=None, number=None):
    return "startmining", [account, password], {'-a':address, '-n':number}, None

@mvs_api_v3
def eth_submit_work(nonce, header_hash, mix_hash):
    '''
    https://github.com/ethereum/wiki/wiki/JSON-RPC#eth_submitwork

    eth_submitWork

    Used for submitting a proof-of-work solution.
    Parameters

        DATA, 8 Bytes - The nonce found (64 bits)
        DATA, 32 Bytes - The header's pow-hash (256 bits)
        DATA, 32 Bytes - The mix digest (256 bits)

    params: [
      "0x0000000000000001",
      "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
      "0xD1FE5700000000000000000000000000D1FE5700000000000000000000000000"
    ]

    Returns

    Boolean - returns true if the provided solution is valid, otherwise false.
    Example

    // Request
    curl -X POST --data '{"jsonrpc":"2.0", "method":"eth_submitWork", "params":["0x0000000000000001", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", "0xD1GE5700000000000000000000000000D1GE5700000000000000000000000000"],"id":73}'

    // Result
    {
      "id":73,
      "jsonrpc":"2.0",
      "result": true
    }

    '''
    return "eth_submitWork", [nonce, header_hash, mix_hash], {}, None

@mvs_api
def submit_work(nonce, header_hash, mix_hash):
    return "submitwork", [nonce, header_hash, mix_hash], {}, None

@mvs_api_v3
def eth_get_work():
    '''
    {"jsonrpc": "2.0", "method": method, "params": params, "id": 0}
    '''
    def result_handler(result):
        header_hash, seed_hash, boundary = result
        return common.toHex(header_hash), seed_hash, boundary

    return "eth_getWork", [], {}, result_handler

@mvs_api
def get_info():
    return "getinfo", [], {}, lambda result: (int(result['height']), int(result['difficulty']))

@mvs_api
def send(account, password, to_, amount, fee=None, desc=None, remark=None):
    positional = [account, password, to_, amount]
    optional =   {
            '-f': fee,
            '-m': desc,
            "-r": remark
        }

    return "send", positional, optional, None

@mvs_api
def sendfrom(account, password, from_, to_, amount, fee=None, desc=None):
    positional = [account, password, from_, to_, amount]
    optional = {
        '-f': fee,
        '-m': desc,
    }

    return "sendfrom", positional, optional, None

@mvs_api
def sendmore(account, password, receivers, mychange=None, fee=None):
    '''

    :param account:
    :param password:
    :param receivers: {address1:amount1, address2:amount2, ...} amount in bits
    :param mychange:
    :param fee:
    :return:
    '''
    positional = [account, password]
    optional = {
        '-f': fee,
        '-m': mychange,
        '-r': ["%s:%s" % (i, receivers[i]) for i in receivers]
    }
    return "sendmore", positional, optional, None

@mvs_api
def didsend(account, password, to_, amount, fee=None, desc=None):
    return "didsend", [account, password, to_, amount], {'-f': fee, '-m': desc}, None

@mvs_api
def didsendmore(account, password, receivers, mychange=None, fee=None):
    '''
    :param receivers: {address1/did1:amount1, address2/did2:amount2, ...} amount in bits
    '''
    optional = {
        '-f': fee,
        '-m': mychange,
        '-r': ["%s:%s" % (i, receivers[i]) for i in receivers]
    }
    return "didsendmore", [account, password], optional, None


@mvs_api
def didsend_from(account, password, from_, to_, amount, fee=None, desc=None):
    return "didsendfrom", [account, password, from_, to_, amount], {'-f': fee, '-m': desc}, None

@mvs_api
def didsend_asset(account, password, to_, symbol, amount, fee=None):
    '''
    :param to_: did or address
    '''
    return "didsendasset", [account, password, to_, symbol, amount], {'--fee': fee}, None

@mvs_api
def didsend_asset_from(account, password, from_, to_, symbol, amount, fee=None):
    '''
    :param from_: did or address
    :param to_: did or address
    '''
    return "didsendassetfrom", [account, password, from_, to_, symbol, amount], {'--fee': fee}, None

@mvs_api
def burn(account, password, symbol, amount):
    return "burn", [account, password, symbol, amount], {}, None

@mvs_api
def gettx(tx_hash, json=None):
    '''
    :param tx_hash: The Base16 transaction hash of the transaction
    :param json: Json/Raw format, default is '--json=true'.
    :return:
    '''
    return "gettx", [tx_hash], {'--json':json}, None

@mvs_api
def listtxs(account, password, address=None, height=None, index=None, limit=None, symbol=None):
    '''
    height:         Get tx according height eg: -e
                     start-height:end-height will return tx between
                     [start-height, end-height)
    '''
    if height != None:
        height = '%s:%s' % (height[0], height[1])

    return "listtxs", [account, password], {
        '-a':address,
        '-e':height,
        '-i':index,
        '-l':limit,
        '-s':symbol
    }, None

@mvs_api
def issue_cert(account, password, to_did, symbol, type, fee=None):
    '''
    account          Account name required.
    password          Account password(authorization) required.
    to_did                Target did
    symbol               Asset cert symbol
    type                 Asset cert type name. eg. NAMING
    '''
    return "issuecert", [account, password, to_did, symbol, type], {'--fee':fee}, None

@mvs_api
def transfer_cert(account, password, to_did, cert_symbol, type, fee=None):
    '''
    :param type: Asset cert type name, eg. ISSUE, DOMAIN, NAMING
    '''
    return "transfercert", [account, password, to_did, cert_symbol, type], {"-f":fee}, None

@mvs_api
def secondary_issue(account, password, to_did, symbol, volume, model=None, fee=None):
    '''
    ACCOUNTNAME          Account name required.
    ACCOUNTAUTH          Account password(authorization) required.
    TODID                target did to check and issue asset, fee from and
                         mychange to the address of this did too.
    SYMBOL               issued asset symbol
    VOLUME               The volume of asset, with unit of integer bits.
    -f [--fee]           The fee of tx. default_value 10000 ETP bits
    -m [--model]         The asset attenuation model parameter, defaults to
                         empty string.
    '''
    return "secondaryissue", [account, password, to_did, symbol, volume], {"-m":model, "-f":fee}, None

@mvs_api
def get_blockheader(hash=None, height=None):
    '''
    -s [--hash]          The Base16 block hash.
    -t [--height]        The block height.
    '''
    return "getblockheader", [], {'-s':hash, '-t':height}, None

@mvs_api
def get_block(hash_or_height, json=True, tx_json=True):
    '''
    HASH_OR_HEIGH        block hash or block height
    JSON                 Json/Raw format, default is '--json=true'.
    TX_JSON              Json/Raw format for txs, default is
                        '--tx_json=true'.
    '''
    return 'getblock', [hash_or_height, json, tx_json], {}, None

@mvs_api
def create_rawtx(receivers, senders, type, deposit=None, fee=None, message=None, mychange=None, symbol=None):
    '''
    -d [--deposit]       Deposits support [7, 30, 90, 182, 365] days.
                         defaluts to 7 days
    -f [--fee]           Transaction fee. defaults to 10000 ETP bits
    -h [--help]          Get a description and instructions for this command.
    -i [--message]       Message/Information attached to this transaction
    -m [--mychange]      Mychange to this address, includes etp and asset
                         change
    -n [--symbol]        asset name, not specify this option for etp tx
    -r [--receivers]     Send to [address:amount]. amount is asset number if
                         sybol option specified
                         receivers -> {addr1:amount1, addr2:amount2, ...}
    -s [--senders]       Send from addresses
                         [addr1, addr2, ...]
    -t [--type]          Transaction type. 0 -- transfer etp, 1 -- deposit
                         etp, 3 -- transfer asset
    '''
    return "createrawtx", [], {
        '-r': ["%s:%s" % (i, receivers[i]) for i in receivers],
        '-s': senders,
        '-t': type,
        '-d': deposit,
        '-f': fee,
        '-i': message,
        '-m': mychange,
        '-n': symbol
    }, None

@mvs_api
def sign_rawtx(account, password, transaction):
    '''
    TRANSACTION          The input Base16 transaction to sign.
    '''
    return "signrawtx", [account, password, transaction], {}, None

@mvs_api
def decode_rawtx(transaction):
    '''
    TRANSACTION          The input Base16 transaction to decode.
    '''
    return "decoderawtx", [transaction], {}, None

@mvs_api
def send_rawtx(transaction, fee=None):
    '''
    TRANSACTION          The input Base16 transaction to broadcast.
    '''
    return "sendrawtx", [transaction], {'-f':fee}, None
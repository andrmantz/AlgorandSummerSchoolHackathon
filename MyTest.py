from algosdk import transaction, account
import algosdk
from algosdk.v2client import *
from pyteal import *
from beaker import *
from beaker import sandbox
from beaker.client import ApplicationClient
from algosdk.transaction import *
from base64 import b64decode
from algosdk.logic import *
from algosdk import constants
import unittest
from algosdk.kmd import KMDClient
import time
from contracts.app import app


def fundApp(client, sender: sandbox.SandboxAccount, AppAddr: str, Ammount):
    txn = transaction.PaymentTxn(sender.address, sp=client.suggested_params(), receiver=AppAddr, amt=Ammount)
    signedTxn = txn.sign(sender.private_key)
    client.send_transaction(signedTxn)
    wait_for_confirmation(client, signedTxn.get_txid())


def addMonster(algod_client, pos_x, pos_y, sender):
    algod_client = sandbox.get_algod_client()
    
    

def getActiveMonstersList(AppID):
    client = sandbox.get_algod_client()
    boxData = b64decode(client.application_box_by_name(AppID, str.encode("MONSTERS"))["value"])

    len = int.from_bytes(boxData[0:8])

    outList = []
    for i in range(8,len*32+8,32):
        outList.append((int.from_bytes(boxData[i:i+8]), int.from_bytes(boxData[i+8:i+16]), int.from_bytes(boxData[i+16:i+24])))

    return outList


def playerOptIn(AppID, playerAccount:sandbox.SandboxAccount):
    client = sandbox.get_algod_client()
    
    sp = client.suggested_params()
    sp.fee = constants.MIN_TXN_FEE * 2
    sp.flat_fee = True

    senderAddr = algosdk.encoding.decode_address(playerAccount.address)

    txn = ApplicationCallTxn(
        sender=playerAccount.address,
        index=AppID,
        sp=sp,
        on_complete=OnComplete.OptInOC.real,
        app_args=[]
    )
    
    signed_txn = txn.sign(playerAccount.private_key)
    client.send_transaction(signed_txn)

    wait_for_confirmation(client, txn.get_txid())


def enterPlayer(AppID, playerAccount:sandbox.SandboxAccount):
    client = sandbox.get_algod_client()
    
    sp = client.suggested_params()
    sp.fee = constants.MIN_TXN_FEE * 2
    sp.flat_fee = True

    senderAddr = algosdk.encoding.decode_address(playerAccount.address)

    txn = ApplicationCallTxn(
        sender=playerAccount.address,
        index=AppID,
        sp=sp,
        on_complete=OnComplete.NoOpOC.real,
        app_args=["enterPlayer()void"],
        boxes=[(0, senderAddr)]
    )
    
    signed_txn = txn.sign(playerAccount.private_key)
    client.send_transaction(signed_txn)

    wait_for_confirmation(client, txn.get_txid())


def exitAndSavePlayer(AppID, playerAccount:sandbox.SandboxAccount):
    client = sandbox.get_algod_client()
    
    sp = client.suggested_params()
    sp.fee = constants.MIN_TXN_FEE * 2
    sp.flat_fee = True

    senderAddr = algosdk.encoding.decode_address(playerAccount.address)
    
    txn = ApplicationCallTxn(
        sender=playerAccount.address,
        index=AppID,
        sp=sp,
        on_complete=OnComplete.NoOpOC.real,
        app_args=["exitAndSavePlayer"],
        boxes=[(0, senderAddr)]
    )

    signed_txn = txn.sign(playerAccount.private_key)
    client.send_transaction(signed_txn)

    wait_for_confirmation(client, txn.get_txid())


def playerMove(AppID, playerAccount:sandbox.SandboxAccount, dir:str):
    client = sandbox.get_algod_client()
    
    txn = ApplicationCallTxn(
        sender=playerAccount.address,
        index=AppID,
        sp=client.suggested_params(),
        on_complete=OnComplete.NoOpOC.real,
        app_args=["playerMove", dir])
    
    signed_txn = txn.sign(playerAccount.private_key)
    client.send_transaction(signed_txn)

    wait_for_confirmation(client, txn.get_txid())


def playerKillMonster(AppID, playerAccount:sandbox.SandboxAccount, monsterASAID):
    client = sandbox.get_algod_client()
    
    sp = client.suggested_params()
    sp.fee = constants.MIN_TXN_FEE * 2
    sp.flat_fee = True

    txn1 = AssetOptInTxn(playerAccount.address, sp=client.suggested_params(), index=monsterASAID)
    txn2 = ApplicationCallTxn(
        sender=playerAccount.address,
        index=AppID,
        sp=sp,
        on_complete=OnComplete.NoOpOC.real,
        app_args=["playerKillMonster"],
        boxes=[(0,0), (0,0), (0,0), (0, algosdk.encoding.decode_address(playerAccount.address)), (0, "MONSTERS")],
        foreign_assets=[monsterASAID]
    )

    txn_list = [txn1, txn2]
    gid = transaction.calculate_group_id(txn_list)
    for t in txn_list:
        t.group = gid

    signedTxnList = [t.sign(playerAccount.private_key) for t in txn_list]
    client.send_transactions(signedTxnList)

    for t in signedTxnList:
        wait_for_confirmation(client, t.get_txid())


def secureAsset(AppID, playerAccount:sandbox.SandboxAccount):
    client = sandbox.clients.get_algod_client()
    p = sandbox.get_algod_client().account_application_info(playerAccount.address, AppID)["app-local-state"]['key-value']
    for v in p:
        if (v["key"] == 'VU5TRUNVUkVEX0FTU0VU'):
            ASA = v["value"]["uint"]
    
    monsterASAID = ASA
    if (monsterASAID == 0):
        return
    
    sp = client.suggested_params()
    sp.fee = constants.MIN_TXN_FEE * 2
    sp.flat_fee = True
    
    txn = ApplicationCallTxn(
        sender=playerAccount.address,
        index=AppID,
        sp=sp,
        on_complete=OnComplete.NoOpOC.real,
        app_args=["secureAsset"],
        foreign_assets=[monsterASAID],
        boxes=[(0,0), (0,0), (0,0), (0, algosdk.encoding.decode_address(playerAccount.address))],
    )

    signedTxnList = txn.sign(playerAccount.private_key)
    client.send_transaction(signedTxnList)

    wait_for_confirmation(client, txn.get_txid())


def playerSteal(AppID, thiefAccount:sandbox.SandboxAccount, victimAddress:str):
    client = sandbox.clients.get_algod_client()
    p = sandbox.get_algod_client().account_application_info(victimAddress, AppID)["app-local-state"]['key-value']
    for v in p:
        if (v["key"] == 'VU5TRUNVUkVEX0FTU0VU'):
            ASA = v["value"]["uint"]
    ASAToSteal = ASA

    sp = client.suggested_params()
    sp.fee = constants.MIN_TXN_FEE * 2
    sp.flat_fee = True

    txn1 = AssetOptInTxn(thiefAccount.address, sp=client.suggested_params(), index=ASAToSteal)
    txn2 = ApplicationCallTxn(
        sender=thiefAccount.address,
        index=AppID,
        sp=sp,
        on_complete=OnComplete.NoOpOC.real,
        app_args=["pvpSteal"],
        accounts = [victimAddress],
        foreign_assets=[ASAToSteal]
    )

    txn_list = [txn1, txn2]
    gid = transaction.calculate_group_id(txn_list)
    for t in txn_list:
        t.group = gid

    signedTxnList = [t.sign(thiefAccount.private_key) for t in txn_list]
    client.send_transactions(signedTxnList)
    
    for t in signedTxnList:
        wait_for_confirmation(client, t.get_txid())
    return wait_for_confirmation(client, txn2.get_txid())




def opt_in_asset(algod_client, account, asa_id: int):
    txn = AssetOptInTxn(account.address, algod_client.suggested_params(), asa_id)
    return algod_client.send_transaction(txn.sign(account.private_key))

if __name__ == "__main__":
    try:
        accounts = sandbox.get_accounts()
        sender = accounts[0]
        
        algod_client = sandbox.get_algod_client()
        # # print(algod_client.application_boxes(AppID))
        
        client = ApplicationClient(algod_client, app, signer= sender.signer, sender=sender.address)
        appId, appAddr, _ = client.create()
        # print(client.get_global_state())
        fundApp(algod_client, sender, appAddr, 100_000_000_000)
        
        client.call("setup", boxes=[(0,0), (0,0), (0,0), (0,0), (0,0), (0,str.encode("MONSTERS"))])
        
        # print(algod_client.application_boxes(appId))
        

        
        for acc in sandbox.get_accounts():
            playerOptIn(appId, acc)
        
        player1 = sandbox.get_accounts()[1]
        player2 = sandbox.get_accounts()[2]
        p1 = algosdk.encoding.decode_address(player1.address)
        p2 = algosdk.encoding.decode_address(player2.address)
        sp = algod_client.suggested_params()
        sp.fee = constants.MIN_TXN_FEE * 2
        client.call("addMonster", pos_x = 5, pos_y = 15, suggested_params=sp ,boxes=[(0,0), (0,0), (0,0), (0,0), (0,0),(0, str.encode("MONSTERS"))])
        client.call("addMonster", pos_x = 15, pos_y = 1024, suggested_params=sp ,boxes=[(0,0), (0,0), (0,0), (0,0), (0,0),(0, str.encode("MONSTERS"))])
        client.call("addMonster", pos_x = 25, pos_y = 143114, suggested_params=sp ,boxes=[(0,0), (0,0), (0,0), (0,0), (0,0),(0, str.encode("MONSTERS"))])
        client.call("addMonster", pos_x = 26, pos_y = 143114, suggested_params=sp ,boxes=[(0,0), (0,0), (0,0), (0,0), (0,0),(0, str.encode("MONSTERS"))])
        client.call("addMonster", pos_x = 123, pos_y = 143114, suggested_params=sp ,boxes=[(0,0), (0,0), (0,0), (0,0), (0,0),(0, str.encode("MONSTERS"))])
        client.call("addMonster", pos_x = 126, pos_y = 143114, suggested_params=sp ,boxes=[(0,0), (0,0), (0,0), (0,0), (0,0),(0, str.encode("MONSTERS"))])
        monsters = algod_client.application_box_by_name(appId, str.encode("MONSTERS"))['value']
        
        dec = b64decode(monsters.encode()).hex()
        counter = int(dec[:16], 16)
        chunks = []
        for i in range(counter*3+1):
            if i == 0:
                continue
            chunks.append(int(dec[i*16:(i+1)*16], 16))
        """
        chunks list explained:
            - Indexes where i%3 == 0 => Pos_x
            - Indexes where i%3 == 1 => Pos_y
            - Indexes where i%3 == 2 => asa_id
        """
        ass1 = chunks[8]
        ass2 = chunks[2]
        opt_in_asset(algod_client, player1, ass1)
        opt_in_asset(algod_client, player1, ass2)
        opt_in_asset(algod_client, player2, ass1)
        opt_in_asset(algod_client, player2, ass2)
        
        enterPlayer(appId, player1)
        # client.call("enterPlayer", sender=player1.address, signer = player1.signer, boxes = [(0, p1)])
        # client.call("enterPlayer", sender=player2.address, signer = player2.signer, boxes = [(0, p2)])
        # client.call("playerKillMonster", sender=player1.address, signer=player1.signer, suggested_params=sp, boxes=[(0,0), (0,0), (0,0), (0,0), (0,0),(0, str.encode("MONSTERS"))], foreign_assets=[ass1])
 
        
    except:
        assert False
    
    AllTests.AppID = AppID
    unittest.main()
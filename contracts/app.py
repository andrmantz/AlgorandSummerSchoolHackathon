#!/usr/bin/env python3

from typing import Final
from pyteal import *
from beaker import *
from contracts.inners import *

class playerData(abi.NamedTuple):
    POS_X: abi.Field[abi.Uint64]
    POS_Y: abi.Field[abi.Uint64]
    UNSECURED_ASSET: abi.Field[abi.Uint64]
    SCORE: abi.Field[abi.Uint64]
    
class monsterData(abi.NamedTuple):
    POS_X: abi.Field[abi.Uint64]
    POS_Y: abi.Field[abi.Uint64]
    ADA_ID: abi.Field[abi.Uint64]
    
class State:
    ADMIN: Final[GlobalStateValue] = GlobalStateValue(
        stack_type=TealType.bytes,
        default=Bytes(""),
        descr="Admin of the game",
    )
    POS_X = LocalStateValue(
        stack_type=TealType.uint64,
        default = Int(0),
        descr="Position X of player"
    )
    POS_Y = LocalStateValue(
        stack_type=TealType.uint64,
        default = Int(0),
        descr="Position Y of player"
    )
    UNSECURED_ASSET = LocalStateValue(
        stack_type=TealType.uint64,
        default = Int(0),
        descr="Player's unsecured asset's ASA id"
    )
    SCORE = LocalStateValue(
        stack_type=TealType.uint64,
        default = Int(0),
        descr = "Player's score"
    )

app = (Application("app", state=State)).apply(unconditional_opt_in_approval, initialize_local_state=True)

@app.create(bare=True)
def create() -> Expr:
    return Seq(
        app.state.ADMIN.set(Txn.sender()),
    )


@Subroutine(TealType.uint64)
def abs(x, y):
    return If(
        x > y, 
        Return(x - y), 
        Return(y - x)
    )
    

@Subroutine(TealType.uint64)
def dist(player1_x, player2_x, player1_y, player2_y):
    return Seq(
        (x_abs := abi.Uint64()).set(abs(player1_x, player2_x)),
        (y_abs := abi.Uint64()).set(abs(player1_y, player2_y)),
        Return(
            (x_abs.get() * x_abs.get()) + (y_abs.get() * y_abs.get())
        )       
    )

@app.external
def setup() -> Expr:
    return Seq(
        Assert(Txn.sender() == app.state.ADMIN),
        
        # Avoid re-initialization by the admin
        length := App.box_length(Bytes("MONSTERS")),
        Assert(Not(length.hasValue())),

        Assert(App.box_create(Bytes("MONSTERS"), Int(4096))),
    )
    
@app.external
def addMonster(pos_x: abi.Uint64, pos_y: abi.Uint64) -> Expr:
    return Seq(
        Assert(Txn.sender() == app.state.ADMIN),
        # Each monster 'struct' is 24 bytes long + 8 bytes the counter.
        (monster_counter := abi.Uint64()).set(Btoi(App.box_extract(Bytes("MONSTERS"), Int(0), Int(8)))),
        create_asset(),
        
        (asa_id := abi.Uint64()).set(InnerTxn.created_asset_id()),
        (new_monster_data := monsterData()).set(pos_x, pos_y, asa_id),
        
        App.box_replace(Bytes("MONSTERS"), Int(0), Itob(monster_counter.get() + Int(1))),
        App.box_replace(Bytes("MONSTERS"), Int(8) + Int(24) * monster_counter.get(), new_monster_data.encode()),
    )

@app.external
def enterPlayer() -> Expr:
    return Seq(
        # If score != 0, then the player is already active
        Assert(app.state.SCORE == Int(0)),
        # If the player does not have a box associated with his address, it's the first time
        contents := App.box_get(Txn.sender()),

        
        If(Not(contents.hasValue()),
           Seq(
            (init_val := abi.Uint64()).set(Int(0)),
            (new_player_data := playerData()).set(init_val, init_val, init_val, init_val),
            App.box_put(Txn.sender(), new_player_data.encode()),
            app.initialize_local_state(),
            app.state.SCORE.set(Int(1)),
            ),
           Seq(
            (pd := playerData()).decode(contents.value()),
            pd.POS_X.store_into(pos_x := abi.Uint64()),
            pd.POS_Y.store_into(pos_y := abi.Uint64()),
            pd.UNSECURED_ASSET.store_into(unsecured_asset := abi.Uint64()),
            pd.SCORE.store_into(score := abi.Uint64()),
            app.state.POS_X.set(pos_x.get()),
            app.state.POS_Y.set(pos_y.get()),
            app.state.UNSECURED_ASSET.set(unsecured_asset.get()),
            app.state.SCORE.set(score.get()),
            App.box_replace(Txn.sender(), Int(0), Itob(Int(0))),
            App.box_replace(Txn.sender(), Int(8), Itob(Int(0))),
            App.box_replace(Txn.sender(), Int(16), Itob(Int(0))),
            App.box_replace(Txn.sender(), Int(24), Itob(Int(0))),
           ),
        )
    )
    
@app.external
def exitAndSavePlayer() -> Expr:
    return Seq(
        Assert(app.state.SCORE != Int(0)),
        (pos_x := abi.Uint64()).set(app.state.POS_X),
        (pos_y := abi.Uint64()).set(app.state.POS_Y),
        (asset := abi.Uint64()).set(app.state.UNSECURED_ASSET),
        (score := abi.Uint64()).set(app.state.SCORE),
        (new_player_data := playerData()).set(pos_x, pos_y, asset, score),  
        App.box_put(Txn.sender(), new_player_data.encode()),
        app.initialize_local_state(),
    )
    
@app.external
def playerMove(direction: abi.String) -> Expr:
    return Seq(
        Assert(app.state.SCORE != Int(0)),
        (up := abi.String()).set("UP"),
        (down := abi.String()).set("DOWN"),
        (right := abi.String()).set("RIGHT"),
        (left := abi.String()).set("LEFT"),
        If(direction.get() == up.get(), app.state.POS_Y.set(app.state.POS_Y.get() + Int(1))),
        If(direction.get() == down.get(), app.state.POS_Y.set(app.state.POS_Y.get() - Int(1))),
        If(direction.get() == right.get(), app.state.POS_X.set(app.state.POS_X.get() + Int(1))),
        If(direction.get() == left.get(), app.state.POS_X.set(app.state.POS_X.get() - Int(1))),
    )
    
@app.external
def playerKillMonster() -> Expr:
    i = ScratchVar(TealType.uint64)
    return Seq(
        Assert(app.state.SCORE != Int(0)),
        Assert(app.state.UNSECURED_ASSET == Int(0)),
        (asaId := abi.Uint64()).set(Txn.assets[Int(0)]),
        (monster_counter := abi.Uint64()).set(Btoi(App.box_extract(Bytes("MONSTERS"), Int(0), Int(8)))),
        Assert(monster_counter.get() > Int(0)),

        (monster_index := abi.Uint64()).set(Int(0)),

        # Look for the asaId in the MONSTERS box
        For(i.store(Int(1)), i.load() < monster_counter.get(), i.store(i.load() + Int(1))).Do(
            Seq(
                (monster_asaId := abi.Uint64()).set(Btoi(App.box_extract(Bytes("MONSTERS"), i.load() * Int(24), Int(8)))),
                If(monster_asaId.get() == asaId.get(), 
                    Seq(
                        monster_index.set(i.load() - Int(1)),
                        Break(),
                    )
                )     
            )
        ),
        
        # Ensure we found the correct monster
        Assert(Btoi(App.box_extract(Bytes("MONSTERS"),  Int(24) * (monster_index.get() + Int(1)), Int(8))) == asaId.get()),
        
        # monster_index now contains the id of the monster to kill
        App.box_replace(Bytes("MONSTERS"), Int(8) + monster_index.get() * Int(24), 
                        App.box_extract(Bytes("MONSTERS"), Int(8) + Int(24) * (monster_counter.get() - Int(1)), Int(24))),
        # Zero out the last monster
        App.box_replace(Bytes("MONSTERS"), Int(8) + (monster_counter.get()-Int(1)) * Int(24), Itob(Int(0))),
        App.box_replace(Bytes("MONSTERS"), Int(16) + (monster_counter.get()-Int(1)) * Int(24), Itob(Int(0))),
        App.box_replace(Bytes("MONSTERS"), Int(24) + (monster_counter.get()-Int(1)) * Int(24), Itob(Int(0))),
        
        App.box_replace(Bytes("MONSTERS"), Int(0), Itob(monster_counter.get() - Int(1))),
        # @TODO Transfer the asset to the owner
        send_asset_transfer_transaction(monster_asaId.get(), Global.current_application_address()),
        app.state.UNSECURED_ASSET.set(asaId.get()),

    )
    
@app.external
def pvpSteal() -> Expr:
    return Seq(
        Assert(app.state.SCORE != Int(0)),
        Assert(app.state.UNSECURED_ASSET == Int(0)),

        (steal_acc := abi.Address()).set(Txn.accounts[0]),
        (steal_asset := abi.Uint64()).set(app.state.UNSECURED_ASSET[steal_acc.get()]),
        Assert(steal_asset.get() != Int(0)),
        
        Assert(app.state.SCORE[steal_acc.get()] != Int(0)),
        
        Assert(dist(app.state.POS_X, app.state.POS_X[steal_acc.get()], app.state.POS_Y, app.state.POS_Y[steal_acc.get()]) <= Int(100)),
        
        send_asset_transfer_transaction(steal_asset.get(), steal_acc.get()),
        
        app.state.UNSECURED_ASSET.set(steal_asset.get()),
        app.state.UNSECURED_ASSET[steal_acc.get()].set(Int(0)),
    )

@app.external
def secureAsset() -> Expr:
    return Seq(
        # Assert(Int(0) == Int(1)),
        # The player has to be active, must hold an asset and 
        # must be inside the safe area in order to call this function
        Assert(app.state.SCORE != Int(0)),
        Assert(app.state.UNSECURED_ASSET != Int(0)),
        Assert(And(app.state.POS_X < Int(11), app.state.POS_Y < Int(11))),
        
        # The asset is now secured, so we clear the local state var
        app.state.UNSECURED_ASSET.set(Int(0)),
        # Player gets 1 point
        app.state.SCORE.set(app.state.SCORE.get() + Int(1)),
    )
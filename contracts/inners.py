from pyteal import *

    
def send_asset_transfer_transaction(asa_id: Expr, sender: Expr):
    return Seq(
        InnerTxnBuilder.Execute(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: asa_id,
                TxnField.asset_sender: sender,
                TxnField.asset_receiver: Txn.sender(),
                TxnField.asset_amount: Int(1),
                TxnField.fee: Int(0),
            }
        )
    )

def create_asset() -> Expr:
    return InnerTxnBuilder.Execute(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_clawback: Global.current_application_address(),
                TxnField.config_asset_manager: Global.current_application_address(),
                TxnField.config_asset_freeze: Global.current_application_address(),
                TxnField.config_asset_reserve: Global.current_application_address(),
                TxnField.config_asset_default_frozen: Int(1),
                TxnField.config_asset_total: Int(1),
                TxnField.fee: Int(0),
            }
        )
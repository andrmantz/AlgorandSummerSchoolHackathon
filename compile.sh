#!/bin/bash

python3 -m contracts.deploy
cp contracts/artifacts/approval.teal contracts/ApprovalProgram.teal 
cp contracts/artifacts/clear.teal contracts/ClearStateProgram.teal
sed -i '' 's/0x1b2fb4f5/"setup"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x083dc404/"addMonster"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0xd6b0e9ca/"enterPlayer"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0xf3bf2fb4/"exitAndSavePlayer"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x674e52e0/"playerMove"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x201cbee5/"playerKillMonster"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x6615b664/"pvpSteal"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x6390997e/"secureAsset"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x00025550/"UP"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x0004444f574e/"DOWN"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x00055249474854/"RIGHT"/g' contracts/ApprovalProgram.teal
sed -i '' 's/0x00044c454654/"LEFT"/g' contracts/ApprovalProgram.teal

rm -rf contracts/artifacts

import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import Context
import asyncio
import boto3
from boto3.dynamodb.conditions import Key, Attr

Access_Key =""
Secret_Key = ""

session = boto3.Session(aws_access_key_id=Access_Key,
                        aws_secret_access_key=Secret_Key,
                        region_name='eu-west-2')
dynamodb = session.resource('dynamodb')
LisBot = commands.Bot(command_prefix='!')
LisDB = dynamodb.Table('LisperroDB')


@LisBot.event
async def on_ready():
    print("Ready")

@LisBot.command(pass_context=True)
async def list(ctx):
    InfoRow = []
    response = LisDB.scan(
        ProjectionExpression= 'GuildImprovements, #l, #u',
        ExpressionAttributeNames={'#l': 'Current Level','#u': 'Upkeep'}
        )
    items = response['Items']
    for count, place in enumerate(items,1):
        if(place['GuildImprovements'] == 'Guild Hall'):
            InfoRow.append(str(count) + ". " + place['GuildImprovements'] + " - Lvl." + str(place['Current Level']) + " - Total Upkeep: " + str(place['Upkeep']) + "gp")
        else:
            InfoRow.append(str(count) + ". " + place['GuildImprovements'] + " - Lvl." + str(place['Current Level']) + " - Upkeep: " + str(place['Upkeep']) + "gp")
    message= "\n".join(InfoRow)
    embededList = discord.Embed(title="List of Buildings", description=message, color=0x35f4ff)
    await LisBot.say(embed = embededList)
    
@LisBot.command(pass_context=True)
async def info(ctx, *,improvName):
    print(improvName)
    response = LisDB.query(
        KeyConditionExpression=Key('GuildImprovements').eq(improvName)
        )
    placeholder = response['Items']
    print(placeholder)
    if not placeholder:
        await LisBot.say("Im sorry, but I can't find that information.")
    else:
        improvInfo = placeholder[0]
        contactName = improvInfo.get('ContactName','')
        infoBlock = discord.Embed(title=improvName,description=improvInfo.get('Description') ,color=0x123456)
        infoBlock.add_field(name="Current Level",value=improvInfo.get('Current Level'),inline=True)
        if(len(contactName)>2):
            infoBlock.add_field(name="Practitioner", value = contactName, inline=True)
        infoBlock.add_field(name="Effect Next Level",value=improvInfo.get('Next Level Bonus'), inline=False)
        infoBlock.add_field(name="Gold Invested",value=str(improvInfo.get('Gold Invested'))+'gp',inline=True)
        if('BaseUpkeep' in improvInfo):
            infoBlock.add_field(name="Total Upkeep",value=str(improvInfo.get('Upkeep'))+'gp',inline=True)
        else:
            infoBlock.add_field(name="Upkeep",value=str(improvInfo.get('Upkeep'))+'gp',inline=True)
        infoBlock.add_field(name="Gold For Next Level",value=str(improvInfo.get('Gold For Next Level'))+'gp',inline=True)

        await LisBot.say(embed = infoBlock)

@LisBot.command(pass_context=True)
async def set(ctx,*, updateVal):
    print(ctx.message.author.top_role)
    top_role = ctx.message.author.top_role
    
    if(str(top_role) != "GM"): #Only those with the role of GM in discord should be able to access this infomation
        await LisBot.say("Sorry you do not have access to that information")
    else:
        updateList = []
        for x in updateVal.split(','):
            updateList.append(x.strip())
        print(updateList)
        if(len(updateList) != 3):
            await LisBot.say("It seems you gave me the wrong amount of information.")
        else:
            LisDB.update_item(
                Key={'GuildImprovements': updateList[0]},
                ConditionExpression = 'attribute_exists({})'.format(updateList[1]),
                UpdateExpression = 'SET {} = :val1'.format(updateList[1]),
                ExpressionAttributeValues={':val1': updateList[2]}
                )
            await LisBot.say("Thanks for the update.")
            
@LisBot.command(pass_context=True)
async def upkeep(ctx):
    response = LisDB.scan(
        ProjectionExpression='Upkeep, BaseUpkeep'
        )
    items = response['Items']
    print(items)
    upkeepSum = 0
    for x in items:
        if('BaseUpkeep' in x):
            upkeepSum = upkeepSum + x.get('BaseUpkeep',0)
        else:
            upkeepSum = upkeepSum + x.get('Upkeep')
    LisDB.update_item(
                Key={'GuildImprovements': 'Guild Hall'},
                UpdateExpression = 'SET Upkeep = :val1',
                ExpressionAttributeValues={':val1': upkeepSum}
                )
    await LisBot.say("I've gone over the accounts and updated the total upkeep.\nTotal Upkeep: {}gp per month".format(upkeepSum))

@LisBot.command(pass_context=True)
async def rent(ctx, rentInput):
    print(ctx.message.author.display_name)
    usr_name = ctx.message.author.display_name
    print(rentInput)
    if(rentInput.isdigit() == False):
        await LisBot.say("The value entered is not a number")
    elif(int(rentInput) == 0):
        await LisBot.say("0 is not an acceptable input")
    else:
        currentEntry = usr_name + ": " + rentInput +"gp  @ " + str(ctx.message.timestamp) +"\n"
        appendFile = open("rent_history.txt", "a")
        appendFile.write(currentEntry)
        appendFile.close()
        readFile = open("rent_history.txt", "r")
        paymentList = readFile.read()
        print(paymentList)
        response = LisDB.get_item(
            Key={'GuildImprovements' : 'Guild Hall'},
            ProjectionExpression='Upkeep, Rent'
            )
        totalRent = response['Item'].get('Upkeep')
        print("total = " + str(totalRent))
        currentRent = int(response['Item'].get('Rent'))
        currentRent = currentRent + int(rentInput)
        print("current = " + str(currentRent))
        LisDB.update_item(
            Key={'GuildImprovements' : 'Guild Hall'},
            UpdateExpression = 'SET Rent = :val1',
            ExpressionAttributeValues={':val1': str(currentRent)}
            )
        rentInfo = "So far you have paid " + str(currentRent) + "gp out of a total of " + str(totalRent) +"gp"
        rentBlock = discord.Embed(title="Summary of Rent", description = rentInfo ,color=0x123456)
        rentBlock.add_field(name="Payment History",value=paymentList,inline=True)
        await LisBot.say(embed = rentBlock)

LisBot.run("") #insert discord api key here
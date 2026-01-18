import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View
from colorama import Fore, Style, init
from datetime import timedelta
from config import TOKEN, PREFIX
from discord.ext import commands
from discord.ui import View, Button
from discord.ui import View, Select
import json

# ================= CONFIG =================

TOKEN = "MTQ1MTk2NTExODA3MzE0MzQzNw.GMbCRA.KY7eUTyucX43P7U_MN2K7JIba1u3DUwU_pdYqk"  # <-- Put your bot token here

# ---------- Console Banner ----------
init(autoreset=True)

def banner():
    print(Fore.GREEN + Style.BRIGHT + r"""
███████╗███╗   ██╗
██╔════╝████╗  ██║
█████╗  ██╔██╗ ██║
██╔══╝  ██║╚██╗██║
██║     ██║ ╚████║
╚═╝     ╚═╝  ╚═══╝
""")
    print(Fore.GREEN + Style.BRIGHT + ">> DEVELOPER BY FN X OJAS")

banner()

# ---------- Bot Setup ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ================= DATA STORAGE FOR NEW FEATURES =================
member_data = {}  # user_id : {"warns":0,"vc_time":0,"chat_messages":0,"abuse":0}
voice_states = {}  # user_id : last join timestamp

# ================= LISTENERS FOR ACTIVITY TRACKING =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    if user_id not in member_data:
        member_data[user_id] = {"warns":0, "vc_time":0, "chat_messages":0, "abuse":0}

    # Count chat messages
    member_data[user_id]["chat_messages"] += 1

    # Simple abuse detection
    abuse_words = ["badword1","badword2"]  # Replace with actual words
    if any(word in message.content.lower() for word in abuse_words):
        member_data[user_id]["abuse"] += 1

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    user_id = member.id

    # VC join
    if after.channel and (before.channel != after.channel):
        voice_states[user_id] = datetime.utcnow()

    # VC leave
    if before.channel and (after.channel != before.channel):
        if user_id in voice_states:
            join_time = voice_states.pop(user_id)
            duration = (datetime.utcnow() - join_time).total_seconds() // 60
            if user_id not in member_data:
                member_data[user_id] = {"warns":0,"vc_time":0,"chat_messages":0,"abuse":0}
            member_data[user_id]["vc_time"] += int(duration)

# ================= NEW COMMANDS =================

# ---------- $SCAN ----------
@bot.command()
@commands.has_permissions(kick_members=True)
async def scan(ctx, member: discord.Member):
    user_id = member.id

    if user_id not in member_data:
        await ctx.send(f"❌ {member.mention} has no recorded data.")
        return

    data = member_data[user_id]

    embed = discord.Embed(
        title=f"🔍 Scan Result: {member}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="User ID", value=str(member.id), inline=False)
    embed.add_field(name="VC Time", value=f"{data['vc_time']} minutes", inline=False)
    embed.add_field(name="Chat Messages", value=str(data['chat_messages']), inline=False)
    embed.add_field(name="Abuse Count", value=str(data['abuse']), inline=False)
    embed.add_field(name="Warns", value=f"{data['warns']}/3", inline=False)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)

# ----------$ WARN ---------
@bot.tree.command(name="scan", description="Scan a member's activity")
async def slash_scan(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="❌ You don't have permission to use this command.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    user_id = member.id

    if user_id not in member_data:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"❌ {member.mention} has no recorded data.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    data = member_data[user_id]

    embed = discord.Embed(
        title=f"🔍 Scan Result: {member}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="User ID", value=str(member.id), inline=False)
    embed.add_field(name="VC Time", value=f"{data['vc_time']} minutes", inline=False)
    embed.add_field(name="Chat Messages", value=str(data['chat_messages']), inline=False)
    embed.add_field(name="Abuse Count", value=str(data['abuse']), inline=False)
    embed.add_field(name="Warns", value=f"{data['warns']}/3", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)

    await interaction.response.send_message(embed=embed)
    
# ----------$ WARN ----------
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    user_id = member.id

    if user_id not in member_data:
        member_data[user_id] = {
            "warns": 0,
            "vc_time": 0,
            "chat_messages": 0,
            "abuse": 0
        }

    member_data[user_id]["warns"] += 1
    warns = member_data[user_id]["warns"]

    # ---------- WARN EMBED (DM) ----------
    warn_embed = discord.Embed(
        title="⚠️ Warning Issued",
        description=f"You have been warned in **{ctx.guild.name}**",
        color=discord.Color.blue()
    )
    warn_embed.add_field(name="Reason", value=reason, inline=False)
    warn_embed.add_field(name="Warn Count", value=f"{warns}/3", inline=False)
    warn_embed.set_footer(text="Please follow the server rules")

    try:
        await member.send(embed=warn_embed)
    except:
        pass

    # ---------- CONFIRM EMBED (CHANNEL) ----------
    confirm_embed = discord.Embed(
        description=f"⚠️ {member.mention} warned (**{warns}/3**)",
        color=discord.Color.blue()
    )
    await ctx.send(embed=confirm_embed)

    # ---------- AUTO TIMEOUT ----------
    if warns >= 3:
        await member.timeout(timedelta(minutes=1))

        timeout_embed = discord.Embed(
            title="⏱ Auto Timeout",
            description=f"You have been timed out for **1 minute** in **{ctx.guild.name}**",
            color=discord.Color.blue()
        )
        timeout_embed.add_field(name="Reason", value="Reached 3 warnings", inline=False)

        try:
            await member.send(embed=timeout_embed)
        except:
            pass

        await ctx.send(
            embed=discord.Embed(
                description=f"⏱ {member.mention} auto-timed out for **1 minute**",
                color=discord.Color.blue()
            )
        )

        # Reset warns
        member_data[user_id]["warns"] = 0
                 
 # ---------- /warn ----------
@bot.tree.command(name="warn", description="Warn a member")
async def slash_warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):
    # ---------- PERMISSION CHECK ----------
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="❌ You don't have permission to use this command.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    user_id = member.id

    if user_id not in member_data:
        member_data[user_id] = {
            "warns": 0,
            "vc_time": 0,
            "chat_messages": 0,
            "abuse": 0
        }

    member_data[user_id]["warns"] += 1
    warns = member_data[user_id]["warns"]

    # ---------- WARN EMBED (DM) ----------
    warn_embed = discord.Embed(
        title="⚠️ Warning Issued",
        description=f"You have been warned in **{interaction.guild.name}**",
        color=discord.Color.blue()
    )
    warn_embed.add_field(name="Reason", value=reason, inline=False)
    warn_embed.add_field(name="Warn Count", value=f"{warns}/3", inline=False)
    warn_embed.set_footer(text="Please follow the server rules")

    try:
        await member.send(embed=warn_embed)
    except:
        pass

    # ---------- CONFIRM EMBED (SLASH RESPONSE) ----------
    await interaction.response.send_message(
        embed=discord.Embed(
            description=f"⚠️ {member.mention} warned (**{warns}/3**)",
            color=discord.Color.blue()
        )
    )

    # ---------- AUTO TIMEOUT ----------
    if warns >= 3:
        await member.timeout(timedelta(minutes=1))

        timeout_embed = discord.Embed(
            title="⏱ Auto Timeout",
            description=f"You have been timed out for **1 minute** in **{interaction.guild.name}**",
            color=discord.Color.blue()
        )
        timeout_embed.add_field(name="Reason", value="Reached 3 warnings", inline=False)

        try:
            await member.send(embed=timeout_embed)
        except:
            pass

        await interaction.followup.send(
            embed=discord.Embed(
                description=f"⏱ {member.mention} auto-timed out for **1 minute**",
                color=discord.Color.blue()
            )
        )

        # Reset warns
        member_data[user_id]["warns"] = 0
                                
# ---------- LOCK ----------
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel locked!")

@bot.tree.command(name="lock", description="Lock the current channel")
async def slash_lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel locked!")

# ---------- UNLOCK ----------
@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Channel unlocked!")

@bot.tree.command(name="unlock", description="Unlock the current channel")
async def slash_unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel unlocked!")

# ---------- GLOBAL SLASH COMMAND SYNC ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced globally ✅")
    except Exception as e:
        print("Error syncing slash commands:", e)

# ================= MANUAL JOIN/LEAVE (Persistent) =================
@bot.command()
async def join(ctx):
    """Bot aapke VC me join kare"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Pehle VC join karein jahan main join karun.")
        return

    vc = ctx.author.voice.channel

    if ctx.guild.voice_client:
        # Agar already same VC me ho to ignore
        if ctx.guild.voice_client.channel.id == vc.id:
            await ctx.send(f"✅ Main already is VC me hoon: {vc.name}")
        else:
            await ctx.guild.voice_client.move_to(vc)
            await ctx.send(f"✅ VC switch kar diya: {vc.name}")
    else:
        await vc.connect()
        await ctx.send(f"✅ Joined VC: {vc.name}")

@bot.command()
async def leave(ctx):
    """Bot VC se leave kare"""
    vc_client = ctx.guild.voice_client
    if vc_client:
        await vc_client.disconnect()
        await ctx.send("👋 VC se leave kar diya.")
    else:
        await ctx.send("❌ Main VC me nahi hoon.")

# ---------------- CONFIG ----------------
config_file = "config.json"

def load_config():
    global config
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"staff_roles": []}
        save_config()

def save_config():
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

load_config()

# ---------------- EVENT ----------------
@bot.event
async def on_member_join(member: discord.Member):
    # DM ko background me bhejne ke liye task
    async def send_dm():
        try:
            embed_dm = discord.Embed(
                title=f"<a:op:1452712544887243006> WELCOME TO {member.guild.name.upper()}! <a:op:1452712544887243006>",
                description=f"👋 Hello {member.name}, welcome to **{member.guild.name}**! <a:Arrowrcolor:1452648668225208351>",
                color=discord.Color.blue()
            )
            if member.guild.icon:
                embed_dm.set_thumbnail(url=member.guild.icon.url)
            embed_dm.set_footer(text="Made by FN")

            file_dm = discord.File("assets/welcome.gif", filename="welcome.gif")
            embed_dm.set_image(url="attachment://welcome.gif")

            await member.send(embed=embed_dm, file=file_dm)
        except discord.Forbidden:
            print(f"Could not DM {member}")

    # Server welcome message
    async def send_server_msg():
        channel_id = config.get("welcome_channel")
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        embed_channel = discord.Embed(
            title=f"<a:op:1452712544887243006> WELCOME TO {member.guild.name.upper()}! <a:op:1452712544887243006>",
            description=f"{member.mention} joined the server! 🎉",
            color=discord.Color.blue()
        )
        if member.guild.icon:
            embed_channel.set_thumbnail(url=member.guild.icon.url)
        embed_channel.set_footer(text="Made by FN")

        file_channel = discord.File("assets/welcome.gif", filename="welcome.gif")
        embed_channel.set_image(url="attachment://welcome.gif")

        await channel.send(content=member.mention, embed=embed_channel, file=file_channel)

    # Run DM immediately in background
    bot.loop.create_task(send_dm())
    # Server message bhi background me run
    bot.loop.create_task(send_server_msg())
    
# ================= COMMANDS =================

# Set welcome channel
@bot.command()
@commands.has_permissions(administrator=True)
async def welcome(ctx, channel: discord.TextChannel):
    config["welcome_channel"] = channel.id
    save_config()
    await ctx.send(f"✅ Welcome channel set to {channel.mention}")  

# ---------------- VIEWS ----------------
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.green,
        custom_id="create_ticket"
    )
    async def create_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild
        user = interaction.user

        # Already open check
        if discord.utils.get(guild.text_channels, name=f"ticket-{user.id}"):
            await interaction.response.send_message(
                "❌ Aapka ticket already open hai",
                ephemeral=True
            )
            return

        # Permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        for role_id in config["staff_roles"]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                )

        # CATEGORY AUTO CREATE / GET
        category = discord.utils.get(guild.categories, name="Tickets")
        if category is None:
            category = await guild.create_category("Tickets")

        # Create channel
        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="Ticket Opened",
            description=f"Hello {user.mention} 👋\nApply for Staff / Complaint Support.\nStaff will reply soon.",
            color=discord.Color.blue()
        )

        await channel.send(
            content=user.mention,
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.red,
        custom_id="close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        user = interaction.user

        allowed = (
            user.guild_permissions.administrator or
            any(r.id in config["staff_roles"] for r in user.roles)
        )

        if not allowed:
            await interaction.response.send_message(
                "❌ Aapko permission nahi hai",
                ephemeral=True
            )
            return

        await interaction.channel.delete()

# ---------------- COMMANDS ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def ticket(ctx):
    """Send ticket panel"""
    embed = discord.Embed(
        title="<a:op:1454901617915854880> Complain / Staff Apply",
        description="<a:op:1454543107738828873>To create a ticket, click the button below",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())


@bot.command()
@commands.has_permissions(administrator=True)
async def staffrole(ctx, role: discord.Role):
    if role.id not in config["staff_roles"]:
        config["staff_roles"].append(role.id)
        save_config()
        await ctx.send(f"✅ Staff role added: {role.mention}")
    else:
        await ctx.send("⚠️ Role already added")


@bot.command()
@commands.has_permissions(administrator=True)
async def removestaff(ctx, role: discord.Role):
    if role.id in config["staff_roles"]:
        config["staff_roles"].remove(role.id)
        save_config()
        await ctx.send(f"✅ Staff role removed: {role.mention}")
    else:
        await ctx.send("⚠️ Role not found")

# ---------- Punishment DM Embed ----------
def punishment_embed(action, reason, server, moderator):
    embed = discord.Embed(title="⚠ Punishment Received", color=discord.Color.blue())
    embed.add_field(name="Action", value=action, inline=False)
    embed.add_field(name="Reason", value=reason if reason else "No reason provided", inline=False)
    embed.add_field(name="Server", value=server, inline=False)
    embed.add_field(name="Moderator", value=moderator, inline=False)
    return embed

# ---------- HELP SELECT VIEW ----------
class HelpSelectView(View):
    def __init__(self, guild_icon_url):
        super().__init__(timeout=None)
        self.guild_icon_url = guild_icon_url

        options = [
            discord.SelectOption(label="Member Commands", description="Show all member commands", emoji="<a:Arrowrcolor:1452711807096455330>"),
            discord.SelectOption(label="Moderator Commands", description="Show all moderator commands", emoji="<a:Arrowrcolor:1452711813702619137>"),
            discord.SelectOption(label="Player / channel Commands", description="Show player and scan commands", emoji="<a:Arrowrcolor:1452711793964355655>")
        ]

        select = Select(
            placeholder="Select a command category...",
            options=options,
            custom_id="help_select"
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        choice = interaction.data["values"][0]
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=self.guild_icon_url)

        if choice == "Member Commands":
            embed.title = "Member Commands"
            embed.color = discord.Color.green()
            embed.add_field(name="<a:op:1452648651481677886> $ping / /ping", value="Bot latency", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $serverinfo / /serverinfo", value="Server info", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $user / /user", value="User info", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $say / /say", value="Bot repeat text", inline=False)

        elif choice == "Moderator Commands":
            embed.title = "Moderator Commands"
            embed.color = discord.Color.red()
            embed.add_field(name="<a:op:1452648651481677886> $ban / /ban", value="Ban member", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $unban / /unban", value="Unban member", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $kick / /kick", value="Kick member", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $timeout / /timeout", value="Timeout member", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $removetimeout / /removetimeout", value="Remove timeout", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $purge / /purge", value="Delete messages", inline=False) 
            embed.add_field(name="<a:op:1452648651481677886> $welcome #channel", value="Set welcome channel", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $staffrole @role", value="Assign staff role", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $removestaff @role", value="Remove staff role", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $ticket #channel", value="Set ticket panel channel", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $join", value="Bot joins your VC", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $leave", value="Bot leaves your VC", inline=False)


        elif choice == "Player / channel Commands":
            embed.title = "Player / channel Commands"
            embed.color = discord.Color.blue()
            embed.add_field(name="<a:op:1452648651481677886> $warn | /warn", value="Member activity scan", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $lock  | /lock", value="Member activity scan", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $unlock | /unlock", value="Member activity scan", inline=False)
            embed.add_field(name="<a:op:1452648651481677886> $scan | /scan", value="Member activity scan", inline=False)
           
        
        embed.set_footer(text="Made by FN | NexafyreZ")
        await interaction.response.send_message(embed=embed, ephemeral=True)
     
 # ---------- On Ready ----------
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="/help | $help"))
    await bot.tree.sync()
    print(f"✅ Bot Online: {bot.user}")
    
# ---------- Mention Detection ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

# TAG + APPLY → DM WEBSITE
    if bot.user in message.mentions and "apply" in message.content.lower():
        try:
            embed = discord.Embed(
                title="Application Panel",
                description="Click the button below to apply on our website.",
                color=discord.Color.blue()
            )

            if message.guild and message.guild.icon:
                embed.set_thumbnail(url=message.guild.icon.url)

            view = View()
            view.add_item(
                discord.ui.Button(
                    label="Apply Now",
                    url="https://bit.ly/NexafyreZ-offical-website",
                    style=discord.ButtonStyle.link
                )
            )

            await message.author.send(embed=embed, view=view)
        except discord.Forbidden:
            pass
        return
    
  # On_message event

# -----------------------------

@bot.event

async def on_message(message):

    # Bot apne messages ignore kare

    if message.author.bot:

        return

    # Agar bot ko tag kiya jaaye

    if bot.user in message.mentions:

        embed = discord.Embed(

            title="Use $help | /help show all commands",

            color=discord.Color.blue()

        )

        embed.set_footer(text="Made by FN | NexafyreZ")

        await message.channel.send(embed=embed)

        return

    # Ensure baki commands kaam kare

    await bot.process_commands(message)
    
# ---------- HELP COMMAND ----------
@bot.command()
async def help(ctx):
    guild_icon = ctx.guild.icon.url if ctx.guild.icon else None
    view = HelpSelectView(guild_icon)
    embed = discord.Embed(
        title="Bot Commands Menu",
        description="Select a category below to see commands",
        color=discord.Color.blue()
    )
    if guild_icon:
        embed.set_thumbnail(url=guild_icon)
    await ctx.send(embed=embed, view=view)

@bot.tree.command(name="help", description="Show all commands")
async def slash_help(interaction: discord.Interaction):
    guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
    view = HelpSelectView(guild_icon)
    embed = discord.Embed(
        title="Bot Commands Menu",
        description="Select a category below to see commands",
        color=discord.Color.blue()
    )
    if guild_icon:
        embed.set_thumbnail(url=guild_icon)
    await interaction.response.send_message(embed=embed, view=view)
        
# ---------- PING ----------
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.tree.command(name="ping", description="Bot latency")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

# ---------- SERVER INFO ----------
@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    embed = discord.Embed(title="📌 Server Info", color=discord.Color.blue())
    embed.add_field(name="Name", value=g.name)
    embed.add_field(name="Members", value=g.member_count)
    embed.add_field(name="Owner", value=g.owner)
    embed.add_field(name="ID", value=g.id)
    await ctx.send(embed=embed)

@bot.tree.command(name="serverinfo", description="Server information")
async def slash_serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title="📌 Server Info", color=discord.Color.blue())
    embed.add_field(name="Name", value=g.name)
    embed.add_field(name="Members", value=g.member_count)
    embed.add_field(name="Owner", value=g.owner)
    embed.add_field(name="ID", value=g.id)
    await interaction.response.send_message(embed=embed)

# ---------- USER ----------
@bot.command()
async def user(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title="👤 User Info", color=discord.Color.blue())
    embed.add_field(name="Username", value=member.name)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%d-%m-%Y"))
    embed.set_thumbnail(url=member.avatar)
    await ctx.send(embed=embed)

@bot.tree.command(name="user", description="User information")
async def slash_user(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title="👤 User Info", color=discord.Color.blue())
    embed.add_field(name="Username", value=member.name)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%d-%m-%Y"))
    embed.set_thumbnail(url=member.avatar)
    await interaction.response.send_message(embed=embed)

# ---------- SAY ----------
@bot.command()
async def say(ctx, *, text):
    await ctx.message.delete()
    await ctx.send(text)

@bot.tree.command(name="say", description="Bot repeat text")
async def slash_say(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(text)

# ---------- PURGE ----------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {len(deleted)-1} messages", delete_after=3)

@bot.tree.command(name="purge", description="Delete messages")
@app_commands.describe(amount="Number of messages to delete")
async def slash_purge(interaction: discord.Interaction, amount: int):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ You don't have permission.",
            ephemeral=True
        )
        return

    if not interaction.guild.me.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ I need Manage Messages permission.",
            ephemeral=True
        )
        return

    if amount <= 0:
        await interaction.response.send_message(
            "❌ Invalid number.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(
        f"🧹 Deleted **{len(deleted)}** messages.",
        ephemeral=True
    )
# ---------- BAN ----------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member} has been banned!")
        try:
            await member.send(embed=punishment_embed("BAN", reason, ctx.guild.name, str(ctx.author)))
        except:
            pass
    except discord.Forbidden:
        await ctx.send("❌ Missing permissions")

@bot.tree.command(name="ban", description="Ban member")
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ No permission", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member} banned")
    try:
        await member.send(embed=punishment_embed("BAN", reason, interaction.guild.name, str(interaction.user)))
    except:
        pass

# ---------- KICK ----------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member} has been kicked!")
        try:
            await member.send(embed=punishment_embed("KICK", reason, ctx.guild.name, str(ctx.author)))
        except:
            pass
    except discord.Forbidden:
        await ctx.send("❌ Missing permissions")

@bot.tree.command(name="kick", description="Kick member")
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ No permission", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member} kicked")
    try:
        await member.send(embed=punishment_embed("KICK", reason, interaction.guild.name, str(interaction.user)))
    except:
        pass

# ---------- TIMEOUT ----------
@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int):
    try:
        duration = timedelta(minutes=minutes)
        await member.timeout(duration)
        await ctx.send(f"⏱ {member} timed out for {minutes} minutes")
        try:
            await member.send(embed=punishment_embed("TIMEOUT", f"{minutes} minutes", ctx.guild.name, str(ctx.author)))
        except:
            pass
    except discord.Forbidden:
        await ctx.send("❌ Missing permissions")

@bot.tree.command(name="timeout", description="Timeout member")
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    await interaction.response.send_message(f"⏱ {member} timed out for {minutes} minutes")
    try:
        await member.send(embed=punishment_embed("TIMEOUT", f"{minutes} minutes", interaction.guild.name, str(interaction.user)))
    except:
        pass

# ---------- REMOVE TIMEOUT ----------
@bot.command()
@commands.has_permissions(moderate_members=True)
async def removetimeout(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"✅ Timeout removed from {member}")
        try:
            await member.send(embed=punishment_embed("TIMEOUT REMOVED", "Timeout lifted", ctx.guild.name, str(ctx.author)))
        except:
            pass
    except discord.Forbidden:
        await ctx.send("❌ Missing permissions")

@bot.tree.command(name="removetimeout", description="Remove timeout")
async def slash_removetimeout(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"✅ Timeout removed from {member}")
    try:
        await member.send(embed=punishment_embed("TIMEOUT REMOVED", "Timeout lifted", interaction.guild.name, str(interaction.user)))
    except:
        pass

# ---------- UNBAN ----------
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    try:
        name, discrim = member_name.split("#")
    except:
        await ctx.send("❌ Use correct format Name#1234")
        return
    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (name, discrim):
            await ctx.guild.unban(user)
            await ctx.send(f"✅ {user} has been unbanned")
            try:
                await user.send(embed=punishment_embed("UNBAN", "You have been unbanned", ctx.guild.name, str(ctx.author)))
            except:
                pass
            return
    await ctx.send("❌ User not found in banned list!")

@bot.tree.command(name="unban", description="Unban member")
async def slash_unban(interaction: discord.Interaction, member_name: str):
    banned_users = await interaction.guild.bans()
    try:
        name, discrim = member_name.split("#")
    except:
        await interaction.response.send_message("❌ Use correct format Name#1234", ephemeral=True)
        return
    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (name, discrim):
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ {user} has been unbanned")
            try:
                await user.send(embed=punishment_embed("UNBAN", "You have been unbanned", interaction.guild.name, str(interaction.user)))
            except:
                pass
            return
    await interaction.response.send_message("❌ User not found in banned list!", ephemeral=True)

# ---------- RUN BOT ----------
bot.run(TOKEN)
import json
import re

import discord

from ai.manager import ask_ai


MAX_MOVES = 50


def extract_json(text: str):
    """
    Extract JSON from an AI response.
    Handles both plain JSON and ```json code blocks.
    """

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object found.")

        return json.loads(text[start:end + 1])


def build_server_structure(guild: discord.Guild):
    """
    Build a snapshot of the current Discord server structure.
    """

    categories = []

    for category in guild.categories:
        channels = []

        for channel in category.channels:
            if isinstance(channel, discord.TextChannel):
                channel_type = "text"

            elif isinstance(channel, discord.VoiceChannel):
                channel_type = "voice"

            else:
                continue

            channels.append({
                "id": channel.id,
                "name": channel.name,
                "type": channel_type
            })

        categories.append({
            "id": category.id,
            "name": category.name,
            "channels": channels
        })

    uncategorized = []

    for channel in guild.channels:
        if channel.category is not None:
            continue

        if isinstance(channel, discord.TextChannel):
            channel_type = "text"

        elif isinstance(channel, discord.VoiceChannel):
            channel_type = "voice"

        else:
            continue

        uncategorized.append({
            "id": channel.id,
            "name": channel.name,
            "type": channel_type
        })

    return {
        "categories": categories,
        "uncategorized": uncategorized
    }


def build_ai_prompt(guild: discord.Guild, structure):
    """
    Create a strict prompt requiring a JSON-only organization plan.
    """

    return f"""
You are the AI Discord Server Organization Planner.

Your job is to analyze the REAL Discord server structure below
and create a safe organization plan.

SERVER NAME:
{guild.name}

CURRENT SERVER STRUCTURE:
{json.dumps(structure, indent=2)}

IMPORTANT RULES:

1. Use ONLY channel IDs and category IDs provided in the server structure.
2. NEVER invent IDs.
3. NEVER rename channels.
4. NEVER delete channels.
5. NEVER change permissions.
6. NEVER change channel types.
7. ONLY suggest moving existing channels into existing categories.
8. Do not create new categories.
9. Do not move channels if they are already in the correct category.
10. Keep the number of moves at or below {MAX_MOVES}.
11. Prefer minimal changes.
12. If the current organization is already good, return an empty moves list.
13. The "reason" should briefly explain why the proposed organization is better.

RETURN ONLY VALID JSON.

Use EXACTLY this structure:

{{
  "moves": [
    {{
      "channel_id": 123456789,
      "target_category_id": 987654321
    }}
  ],
  "reason": "Brief explanation of the proposed organization."
}}

The IDs above are examples only.
Use the REAL IDs from the server structure.

Do not include Markdown.
Do not include ```json.
Do not include any text outside the JSON object.
"""


def validate_plan(
    guild: discord.Guild,
    structure,
    plan
):
    """
    Validate the AI-generated plan before anything is changed.
    """

    if not isinstance(plan, dict):
        return False, "AI returned an invalid plan."

    moves = plan.get("moves")

    if not isinstance(moves, list):
        return False, "AI plan does not contain a valid moves list."

    if len(moves) > MAX_MOVES:
        return False, f"AI requested more than {MAX_MOVES} channel moves."

    if not isinstance(plan.get("reason"), str):
        return False, "AI plan does not contain a valid reason."

    valid_channel_ids = set()
    valid_category_ids = set()

    for category in structure["categories"]:
        valid_category_ids.add(category["id"])

        for channel in category["channels"]:
            valid_channel_ids.add(channel["id"])

    for channel in structure["uncategorized"]:
        valid_channel_ids.add(channel["id"])

    seen_channels = set()

    for move in moves:

        if not isinstance(move, dict):
            return False, "A move entry is invalid."

        channel_id = move.get("channel_id")
        target_category_id = move.get(
            "target_category_id"
        )

        if not isinstance(channel_id, int):
            return False, "A channel ID is invalid."

        if not isinstance(target_category_id, int):
            return False, "A category ID is invalid."

        if channel_id not in valid_channel_ids:
            return False, (
                f"AI referenced an unknown channel ID: "
                f"{channel_id}"
            )

        if target_category_id not in valid_category_ids:
            return False, (
                f"AI referenced an unknown category ID: "
                f"{target_category_id}"
            )

        if channel_id in seen_channels:
            return False, (
                f"Channel {channel_id} appears more than once."
            )

        seen_channels.add(channel_id)

    return True, None


class OrganizationView(discord.ui.View):

    def __init__(
        self,
        author_id: int,
        guild: discord.Guild,
        plan: dict
    ):
        super().__init__(timeout=120)

        self.author_id = author_id
        self.guild = guild
        self.plan = plan

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id != self.author_id:

            await interaction.response.send_message(
                "❌ Only the person who created this proposal "
                "can use these buttons.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Confirm",
        emoji="✅",
        style=discord.ButtonStyle.success
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            view=self
        )

        guild = self.guild

        me = guild.me

        if me is None:
            await interaction.followup.send(
                "❌ I couldn't verify my permissions."
            )
            return

        if not me.guild_permissions.manage_channels:
            await interaction.followup.send(
                "❌ I need the **Manage Channels** permission "
                "to apply this organization."
            )
            return

        try:
            await guild.fetch_channels()

        except Exception as e:
            print("----------------------------------------")
            print("❌ Failed to refresh channels")
            print(e)
            print("----------------------------------------")

            await interaction.followup.send(
                "❌ I couldn't refresh the server's channels "
                "before applying the changes."
            )

            return

        current_channels = {
            channel.id: channel
            for channel in guild.channels
        }

        current_categories = {
            category.id: category
            for category in guild.categories
        }

        moves = self.plan.get("moves", [])

        if not moves:
            await interaction.followup.send(
                "ℹ️ There are no channel moves to apply."
            )
            return

        moved = 0
        failed = 0
        skipped = 0

        for move in moves:

            channel_id = move["channel_id"]
            target_category_id = move[
                "target_category_id"
            ]

            channel = current_channels.get(
                channel_id
            )

            category = current_categories.get(
                target_category_id
            )

            if channel is None:
                failed += 1
                print(
                    f"❌ Channel {channel_id} no longer exists."
                )
                continue

            if category is None:
                failed += 1
                print(
                    f"❌ Category {target_category_id} "
                    f"no longer exists."
                )
                continue

            if channel.category_id == category.id:
                skipped += 1
                continue

            try:

                await channel.edit(
                    category=category,
                    reason=(
                        "AI Server Assistant "
                        "organization"
                    )
                )

                moved += 1

                print(
                    f"✅ Moved #{channel.name} "
                    f"→ {category.name}"
                )

            except discord.Forbidden:

                failed += 1

                print(
                    f"❌ Permission denied for "
                    f"#{channel.name}"
                )

            except discord.HTTPException as e:

                failed += 1

                print(
                    f"❌ Discord error moving "
                    f"#{channel.name}: {e}"
                )

        result = (
            "## ✅ Organization Applied\n\n"
            f"**Moved:** {moved}\n"
            f"**Skipped:** {skipped}\n"
            f"**Failed:** {failed}"
        )

        await interaction.followup.send(
            result
        )

    @discord.ui.button(
        label="Cancel",
        emoji="❌",
        style=discord.ButtonStyle.danger
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            view=self
        )

        await interaction.followup.send(
            "❌ **Organization proposal cancelled.**\n\n"
            "No channels were changed."
        )

    async def on_timeout(self):

        for item in self.children:
            item.disabled = True


def create_proposal_text(
    guild: discord.Guild,
    plan: dict
):
    """
    Convert the validated JSON plan into a readable proposal.
    """

    moves = plan.get("moves", [])

    if not moves:
        return (
            "## 🧠 AI Organization Proposal\n\n"
            "Your server already looks reasonably organized. "
            "No channel moves are recommended.\n\n"
            f"**Why:** {plan['reason']}"
        )

    lines = [
        "## 🧠 AI Organization Proposal",
        "",
        "The AI recommends these channel moves:",
        ""
    ]

    channels_by_id = {
        channel.id: channel
        for channel in guild.channels
    }

    categories_by_id = {
        category.id: category
        for category in guild.categories
    }

    for move in moves:

        channel = channels_by_id.get(
            move["channel_id"]
        )

        category = categories_by_id.get(
            move["target_category_id"]
        )

        if channel is None or category is None:
            continue

        current_category = (
            channel.category.name
            if channel.category
            else "Uncategorized"
        )

        lines.append(
            f"• **#{channel.name}**\n"
            f"  `{current_category}` → "
            f"`{category.name}`"
        )

    lines.extend([
        "",
        f"**Why:** {plan['reason']}",
        "",
        "⚠️ **No changes have been made yet.**",
        "Press **Confirm** to apply the proposed moves."
    ])

    return "\n".join(lines)


async def setup(bot):

    @bot.tree.command(
        name="organize",
        description=(
            "Ask AI for a safe channel organization proposal."
        )
    )
    async def organize(
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used inside a server."
            )
            return

        me = guild.me

        if me is None:
            await interaction.response.send_message(
                "❌ I couldn't verify my permissions."
            )
            return

        if not me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "❌ I need the **Manage Channels** permission "
                "to organize channels."
            )
            return

        await interaction.response.defer()

        try:

            structure = build_server_structure(
                guild
            )

            prompt = build_ai_prompt(
                guild,
                structure
            )

            print("----------------------------------------")
            print("🧠 Generating organization plan...")
            print("----------------------------------------")

            result = await ask_ai(
                prompt,
                history=[]
            )

            answer = result.get("answer")
            provider = result.get("provider")

            if not answer:

                await interaction.followup.send(
                    "❌ All AI providers are currently "
                    "unavailable. No changes were made."
                )

                return

            print("----------------------------------------")
            print(
                f"🤖 Organization provider: {provider}"
            )
            print("----------------------------------------")

            try:

                plan = extract_json(
                    answer
                )

            except Exception as e:

                print("----------------------------------------")
                print("❌ Failed to parse AI JSON")
                print(e)
                print("AI response:")
                print(answer)
                print("----------------------------------------")

                await interaction.followup.send(
                    "❌ The AI returned an invalid "
                    "organization plan.\n\n"
                    "🛡️ No changes were made."
                )

                return

            valid, error = validate_plan(
                guild,
                structure,
                plan
            )

            if not valid:

                print("----------------------------------------")
                print("❌ AI organization plan failed validation")
                print(f"Reason: {error}")
                print("----------------------------------------")

                await interaction.followup.send(
                    "❌ The AI organization plan failed "
                    "safety validation.\n\n"
                    f"**Reason:** {error}\n\n"
                    "🛡️ **No changes were made.**"
                )

                return

            proposal = create_proposal_text(
                guild,
                plan
            )

            embed = discord.Embed(
                title="🧠 AI Organization Proposal",
                description=proposal[:4000],
                color=discord.Color.blurple()
            )

            embed.set_footer(
                text=(
                    f"AI provider: {provider} • "
                    "Review before confirming"
                )
            )

            view = OrganizationView(
                author_id=interaction.user.id,
                guild=guild,
                plan=plan
            )

            await interaction.followup.send(
                embed=embed,
                view=view
            )

            print("----------------------------------------")
            print("✅ ORGANIZATION PROPOSAL CREATED")
            print(f"Provider: {provider}")
            print(f"Moves: {len(plan['moves'])}")
            print("----------------------------------------")

        except Exception as e:

            print("----------------------------------------")
            print("❌ ORGANIZE COMMAND ERROR")
            print(e)
            print("----------------------------------------")

            await interaction.followup.send(
                "❌ Something went wrong while creating "
                "the organization proposal.\n\n"
                "🛡️ No changes were made."
            )
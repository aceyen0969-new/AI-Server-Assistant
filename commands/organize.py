import json
import uuid

import discord

from ai.providers import (
    ask_gemini,
    ask_openrouter_json,
    ask_groq_json
)

from security.actions import (
    ActionRequest,
    evaluate_action
)

from security.approval import (
    create_approval_request
)

from security.approval_view import (
    ApprovalView
)


async def setup(bot):

    @bot.tree.command(
        name="organize",
        description="Ask the AI to suggest safe server organization changes."
    )
    async def organize(interaction: discord.Interaction):

        await interaction.response.defer()

        guild = interaction.guild

        if guild is None:
            await interaction.followup.send(
                "❌ This command can only be used inside a server."
            )
            return

        categories = []

        for category in guild.categories:
            categories.append({
                "id": category.id,
                "name": category.name
            })

        channels = []

        for channel in guild.channels:
            if isinstance(
                channel,
                (
                    discord.TextChannel,
                    discord.VoiceChannel,
                    discord.StageChannel,
                    discord.ForumChannel
                )
            ):
                channels.append({
                    "id": channel.id,
                    "name": channel.name,
                    "type": str(channel.type),
                    "category_id": (
                        channel.category.id
                        if channel.category
                        else None
                    ),
                    "category_name": (
                        channel.category.name
                        if channel.category
                        else "No Category"
                    )
                })

        server_context = {
            "server_name": guild.name,
            "categories": categories,
            "channels": channels
        }

        prompt = f"""
You are organizing a Discord server.

SERVER INFORMATION:
{json.dumps(server_context, indent=2)}

Your job is to identify channels that appear to be in
the wrong category.

Return ONLY a JSON object using exactly this structure:

{{
    "changes": [
        {{
            "channel_id": 123456789,
            "channel_name": "gaming",
            "current_category_id": 111111111,
            "current_category_name": "Voice Channels",
            "new_category_id": 222222222,
            "new_category_name": "Text Channels",
            "reason": "The channel is a text channel but is currently under a voice category."
        }}
    ]
}}

Rules:

- Only suggest changes that are clearly useful.
- Use the REAL channel and category IDs supplied above.
- Never invent IDs.
- Do not create categories.
- Do not delete channels.
- Do not rename channels.
- Do not modify permissions.
- If no changes are needed, return:
{{"changes": []}}
"""

        providers = [
            ("Gemini", ask_gemini),
            ("OpenRouter", ask_openrouter_json),
            ("Groq", ask_groq_json)
        ]

        result = None
        provider_used = None
        errors = []

        for provider_name, provider_function in providers:
            try:
                print("----------------------------------------")
                print(f"🤖 Organize trying {provider_name}...")

                raw_response = await provider_function(prompt)

                result = json.loads(raw_response)
                provider_used = provider_name

                print(
                    f"✅ Organize response from {provider_name}"
                )

                break

            except Exception as e:
                error_text = str(e)
                errors.append(
                    f"{provider_name}: {error_text}"
                )

                print(
                    f"❌ Organize {provider_name} failed:"
                )
                print(error_text)

        if result is None:
            await interaction.followup.send(
                "❌ The AI organization planner failed.\n\n"
                + "\n".join(errors)
            )
            return

        changes = result.get("changes", [])

        if not changes:
            await interaction.followup.send(
                "✅ The AI found no obvious channel organization changes."
            )
            return

        approved_requests = []

        for change in changes:

            channel_id = change.get("channel_id")
            new_category_id = change.get("new_category_id")

            channel = guild.get_channel(channel_id)
            new_category = guild.get_channel(new_category_id)

            if channel is None:
                continue

            if not isinstance(
                new_category,
                discord.CategoryChannel
            ):
                continue

            action_request = ActionRequest(
                action="move_channel",
                target_id=channel.id,
                target_name=channel.name,
                reason=change.get(
                    "reason",
                    "AI suggested reorganizing this channel."
                ),
                data={
                    "new_category_id": new_category.id,
                    "new_category_name": new_category.name
                }
            )

            decision = evaluate_action(
                action_request
            )

            if not decision["requires_approval"]:
                continue

            request_id = str(uuid.uuid4())

            create_approval_request(
                request_id=request_id,
                action=action_request.action,
                target_id=action_request.target_id,
                target_name=action_request.target_name,
                reason=action_request.reason,
                data=action_request.data
            )

            approved_requests.append(
                (
                    request_id,
                    action_request,
                    new_category
                )
            )

        if not approved_requests:
            await interaction.followup.send(
                "⚠️ The AI returned changes, but none passed "
                "the safety validation."
            )
            return

        for (
            request_id,
            action_request,
            new_category
        ) in approved_requests:

            embed = discord.Embed(
                title="🛡️ AI Organization Request",
                description=(
                    f"**Action:** `move_channel`\n"
                    f"**Channel:** {action_request.target_name}\n"
                    f"**New Category:** {new_category.name}\n"
                    f"**Reason:** {action_request.reason}\n\n"
                    "⚠️ This change requires server-owner approval."
                ),
                color=discord.Color.orange()
            )

            embed.set_footer(
                text=f"AI Provider: {provider_used}"
            )

            view = ApprovalView(
                request_id=request_id,
                allowed_user_id=guild.owner_id,
                guild=guild
            )

            await interaction.followup.send(
                embed=embed,
                view=view
            )

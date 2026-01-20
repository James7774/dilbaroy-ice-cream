
    data = db.load_data()
    contacts = data.get("contacts", [])
    
    if not contacts:
        await update.message.reply_text(
            "📭 Hozircha kontaktlar yo'q",
            parse_mode='Markdown'
        )
        return
    
    # So'nggi 15 ta kontakt
    recent_contacts = contacts[-15:]
    
    contacts_text = f"📞 *BARCHA KONTAKTLAR* ({len(contacts)} ta)\n\n"
    
    for i, contact in enumerate(recent_contacts[::-1], 1):
        contacted_emoji = "✅" if contact.get("contacted") else "❌"
        
        contacts_text += f"""
{i}. {contacted_emoji} *#{contact.get('id', 'N/A')}* - {contact.get('name', 'Noma\'lum')}
   📞 {contact.get('phone', 'N/A')}
   📅 {contact.get('date', 'N/A')}
   💬 {contact.get('message', '')[
'''
i pip installed python-telegram-bot library instead of telepot
telepot seem to have conflicting issues with other libraries on my machine.
python-telegram-bot has apscheduler built in so no need to install it separately.
'''

import requests
import time
from telegram import Update 
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

#  Important keys
ETHERSCAN_API_KEY = ''
TELEGRAM_BOT_TOKEN = ''

#  Logging Setup to check for errors and print logs in the console
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


last_fast_gas_price = None #storing the last fast gas price to calculate change

# Bot Command Handlers 

# Start command is automaitcally entered when the bot is started
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    #apscheduler job to send gas price updates every 2 minutes
    context.job_queue.run_repeating(send_gas_price_update, interval=120, first=1, chat_id=chat_id, name=str(chat_id))
    await update.message.reply_text("Started sending gas price updates every 2 minutes. Use /stop to disable.") #first message to user

# Stop command to stop the gas price updates
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id # Get the chat ID from the update

    # Check if there are any jobs scheduled for this chat ID
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if not current_jobs:
        await update.message.reply_text("No active tasks to stop.") #if no jobs are scheduled run this.
        return
    for job in current_jobs: #if jobs are scheduled, stop them them
        job.schedule_removal()
    await update.message.reply_text("Stopped sending gas price updates.")


#  Main Logic for sending gas prices 
async def send_gas_price_update(context: ContextTypes.DEFAULT_TYPE):
    global last_fast_gas_price
    job = context.job
    url = f'https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={ETHERSCAN_API_KEY}'
    
    try:
        response = requests.get(url) # Fetching gas price data from Etherscan API
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json() # Parsing the JSON response

        if data['status'] == '1': # Check if the API call was successful
            current_fast_gas_price = float(data['result']['FastGasPrice']) # Extract the fast gas price
            gas_used_ratio = float(data['result']['gasUsedRatio'].split(',')[0]) # Extract the gas used ratio.
            
            change = 0.0 #
            if last_fast_gas_price is not None:
                change = current_fast_gas_price - last_fast_gas_price # Calculate the changes in gas price

            message = (f"Nathbob's Gas Price Tracking Bot" "\n"
                       "\n"
                       f"FastGasPrice: {current_fast_gas_price:.2f}, "
                       f"GasUsedRatio: {gas_used_ratio:.2f}, "
                       f"Change: {change:.2f}")

            await context.bot.send_message(job.chat_id, text=message) # Send the message to the user
            
            last_fast_gas_price = current_fast_gas_price
        else:
            logging.warning(f"API Error: {data['message']}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

#  setting up command handler in the main application 
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build() #building the application with the bot token

    application.add_handler(CommandHandler("start", start)) # command to start gas price updates
    application.add_handler(CommandHandler("stop", stop)) # command to stop gas price updates

    application.run_polling() # Start the bot and listen for messages

if __name__ == '__main__':
    main()
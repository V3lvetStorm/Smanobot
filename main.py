#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from imageresizer import imageresize
import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
import logging, os, glob, os, re, urllib.request, time, subprocess
from bs4 import BeautifulSoup


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

IMAGEPROCESSING, SCRAPERPROCESS, ENHANCE = range(3)

### Permission management
global whitelist
whitelist = []
global token
token = "null"
##à


### Array e var globali per il multithread ###
global counter
counter = 0

global process_stop
process_stop = {}

global webm_conversion
webm_conversion = {}
###

def start(update, context):
    update.message.reply_text('Benvenutə.\n'
    'Elenco comandi: \n/start - Avvia il bot\n'
    '/imageprocessing - Modalità creazione stickers\n'
    '/scraper - Scraping threads 4Chan\n'
    '/webm_conversion_on - Abilita webm to mp4\n'
    '/webm_conversion_off - Disabilita webm to mp4\n')

    return ConversationHandler.END

def imageselect(update, context):
    update.message.reply_text(
        'Invia le foto:',
        reply_markup=ReplyKeyboardRemove()
    )

    return IMAGEPROCESSING

def imageprocessing(update, context):
    user = update.message.from_user
    if hasattr(update.message, 'photo'):
        immagine = update.message.photo[-1].file_id
        photo_file = context.bot.get_file(immagine)
        photo_file.download(immagine + ".jpg")
        logging.info("Photo of %s: %s", user.first_name, immagine + '.jpg')
        immagine = immagine + ".jpg"
    else:
        immagine = update.message.document.file_id
        photo_file = context.bot.get_file(immagine)
        photo_file.download(update.message.document.file_name)
        logging.info("File: %s", update.message.document.file_name)
        immagine = update.message.document.file_name

    imageresized = imageresize(immagine)
    context.bot.send_document(chat_id=update.message.chat_id, document=open(imageresized, 'rb'))
    os.remove(imageresized)
    os.remove(immagine)

    cancel_keyboard = [['Annulla']]
    update.message.reply_text(
        'Grazie per la foto!',
        reply_markup=ReplyKeyboardMarkup(cancel_keyboard, one_time_keyboard=True)
    )

    return IMAGEPROCESSING

def urlselect(update, context):
    user = update.message.from_user
    update.message.reply_text('Inserisci url thread',  reply_markup=ReplyKeyboardRemove())

    return SCRAPERPROCESS

#def scraperprocess(update, context):

#@run_async # permette di avviare la funzione sottostante in maniera asincrona
def scraperprocess(update, context):
    user = update.message.from_user

    ##############################
    # Inizializzazione interrupt #
    ##############################
    # Dizionario
    global process_stop
    # Per sicurezza il valore corrispondente all'utente attuale
    # della funzione viene 'disattivato' (reinizializzazione)
    process_stop[user.id] = False

    # Variabile globale che permette di tenere conto di quante operazioni in parallelo sono state avviate
    # Finalità di logging
    global counter
    threadID = counter

    global webm_conversion

    ###
    logging.info("PID {} | Link: {}".format(threadID, update.message.text))
    ###

    # Blocco che permette di analizzare il link inserito
    request = urllib.request.Request(update.message.text, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(request).read()
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', class_="fileThumb")
    thread_name_box = soup.find('span', attrs={'class':'subject'})
    thread_name = thread_name_box.text
    thread_name = re.sub(r'[\\/*?:"<>|]',"", thread_name)
    if thread_name == "":
        thread_name = thread_name = update.message.text.split('/')[-1]
    update.message.reply_text('Thread selezionato: {}'.format(thread_name))

    # Blocco che inizializza la destinazione dei file da scaricare
    destination = "scraper/" + thread_name
    logging.info("PID {} | Inizializzo destinazione... {}".format(threadID, destination))
    if not os.path.exists(destination):
        os.makedirs(destination)

    # Loop di download dei file del thread precedentemente indicato
    for i,link in enumerate(links):
        # Controllo dell'interrupt
        if process_stop[user.id]:
            logging.info("PID {} | Download stoppato".format(threadID))
            update.message.reply_text('Download interrotto!')
            break

        url = link['href']
        if not url.startswith('http'):
            url = "https:{}".format(url)
        file_request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        file_data = urllib.request.urlopen(file_request).read()

        comp = url.split("/")[-1]
        try:
            f=open(os.path.join(destination, '{}'.format(comp)), 'wb')
            f.write(file_data)
            ### Opzione Conversione WEBM #######################################
            try:
                if webm_conversion[user.id]:
                    if comp.split(".")[-1] == "webm":
                        logging.info("Webm rilevato! Tento conversione...")
                        try:
                            print("ffmpeg -n -i "+"\""+destination+"/"+comp+"\""+" "+"\""+destination+"/"+comp.split(".")[-2]+".mp4"+"\"")
                            conversion = subprocess.run("ffmpeg -i "+"\""+destination+"/"+comp+"\""+" -vf \"scale=trunc(iw/2)*2:trunc(ih/2)*2\" "+"\""+destination+"/"+comp.split(".")[-2]+".mp4"+"\"", shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)
                            output = conversion.stdout
                            try:
                                os.remove(destination+"/"+comp)
                                logging.info("Rimozione vecchio webm completata")
                            except:
                                logging.warning("Errore rimozione webm residuo!")
                            comp = comp.split(".")[-2]+".mp4"
                            logging.info("Webm convertito!")
                        except:
                            logging.warning("Errore conversione Webm!")
            except:
                print()
             ###################################################################
        finally:
            f.close()

        ###
        logging.info("PID {} | Scaricato: {}".format(threadID, comp))
        ###

        # Invio dei file
        try:
            context.bot.send_document(chat_id=update.message.chat_id, document=open(os.path.join(destination, comp), 'rb'), timeout=60, reply_to_message_id=update.message.message_id)
            logging.info("PID {} | File {} inviato al destinatario".format(threadID, comp))
        except:
            logging.warning("PID {} | Errore nell'invio di: {}".format(threadID, comp))

    # Fine del processo. Risposte allo user e chiusura della funzione
    if process_stop[user.id]:
        update.message.reply_text('{} file scaricati.'.format(str(i)))
    else:
        update.message.reply_text('Download Completato! {} file scaricati.'.format(str(i)))

    #Pulizia del counter
    counter -= 1

    return ConversationHandler.END

# Opzione conversione dei WEBM in MP4 ###################
def webm_conversion_on(update, context):
    global webm_conversion
    user = update.message.from_user
    webm_conversion[user.id] = True
    logging.info("Valore di webm_conversion per {}: {}".format(user.id, webm_conversion[user.id]))
    update.message.reply_text('Conversione webm attivata',
                              reply_markup=ReplyKeyboardRemove())

    return

def webm_conversion_off(update, context):
    global webm_conversion
    user = update.message.from_user
    webm_conversion[user.id] = False
    logging.info("Valore di webm_conversion per {}: {}".format(user.id, webm_conversion[user.id]))
    update.message.reply_text('Conversione webm disattivata',
                              reply_markup=ReplyKeyboardRemove())

    return

def repost(update, context):
    global channel, whitelist
    user = update.message.from_user
    #update.user.copy_message(chat_id='-1001222460609', message_id=message)
    #channel = open("channel", "r")
    #temp = channel.read().splitlines()
    #channel_id = temp[0]
    #channel.close()
    if user.username in whitelist:
        context.bot.copy_message(chat_id=channel, from_chat_id=update.message.reply_to_message.chat.id, message_id=update.message.reply_to_message.message_id)
    else:
        update.message.reply_text(
        'Mi dispiace bel. Temo di non poterlo fare'
        )

    return ConversationHandler.END
def enhance_query(update, context):
    update.message.reply_text(
        'Inserisci immagine da smarmellare'
    )

    return ENHANCE

def enhance(update, context):
    user = update.message.from_user
    if hasattr(update.message, 'photo'):
        immagine = update.message.photo[-1].file_id
        photo_file = context.bot.get_file(immagine)
        photo_file.download(immagine + ".jpg")
        logging.info("Photo of %s: %s", user.first_name, immagine + '.jpg')
        immagine = immagine + ".jpg"
    else:
        immagine = update.message.document.file_id
        photo_file = context.bot.get_file(immagine)
        photo_file.download(update.message.document.file_name)
        logging.info("File: %s", update.message.document.file_name)
        immagine = update.message.document.file_name

    enhancing = subprocess.run("liquid-rescale "+immagine+" "+immagine+".gif", shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)
    output = enhancing.stdout

    context.bot.send_document(chat_id=update.message.chat_id, document=open(immagine+".gif", 'rb'))
    os.remove(immagine)
    os.remove(immagine+".gif")

    return ConversationHandler.END


def cancel(update, context):
    user = update.message.from_user
    logging.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye dudinə', reply_markup=ReplyKeyboardRemove())
    process_stop[user.id] = True

    return ConversationHandler.END

def init(): # To retrieve BOT token from file
    logging.info("Init...")
    global token, whitelist, channel
    # init token
    token = open("token", "r")
    temp = token.read().splitlines()
    token = temp[0] # avoid the \n at the hand of the file reading
    logging.info("Token loaded: {}".format(token))
    # init user whitelist
    utenti = open("whitelist", "r")
    lines = utenti.readlines()
    for i in lines:
        whitelist.append(i.strip())
        logging.info("User loaded: {}".format(i.strip()))
    # init channel
    channel = open("channel", "r")
    temp = channel.read().splitlines()
    channel = temp[0]
    logging.info("Channel id loaded: {}".format(channel))
    return 0

def main():
    #
    global token, whitelist, channel
    init()
    updater = Updater(token) # loads bot token in the updater
    dispatcher = updater.dispatcher # simplify the dispatcher syntax
    # Command handling section #
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('imageprocessing', imageselect),
            CommandHandler('scraper', urlselect),
            CommandHandler('webm_conversion_on', webm_conversion_on),
            CommandHandler('webm_conversion_off', webm_conversion_off),
            CommandHandler('repost', repost),
            CommandHandler('enhance', enhance_query)
        ],

        states={
            IMAGEPROCESSING: [MessageHandler(Filters.document.category("image") | Filters.photo, imageprocessing)],
            SCRAPERPROCESS: [MessageHandler(Filters.text, scraperprocess, run_async=True)],
            ENHANCE: [MessageHandler(Filters.document.category("image") | Filters.photo, enhance, run_async=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(Filters.text('Annulla'), cancel)]

    )
    #start_handler = CommandHandler('start', start) # create an handler
    dispatcher.add_handler(conv_handler) # add handler to dispatcher
    updater.start_polling() # the bot start watching...
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()


import os
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib
from inaSpeechSegmenter import Segmenter
from inaSpeechSegmenter.constants import ResultFrame
from telegram import Update, Message
from telegram.ext import Updater, CallbackContext, Dispatcher, CommandHandler, MessageHandler, \
    Filters

from bot import utils
from bot.render import draw_ml


def segment(file) -> list[ResultFrame]:
    return [ResultFrame(*s) for s in seg(file)]


def r(u: Update, msg: str, md=True):
    updater.bot.sendMessage(chat_id=u.effective_chat.id, text=msg,
                            parse_mode='Markdown' if md else None)


def cmd_start(u: Update, c: CallbackContext):
    r(u, '欢迎! 点下面的录音按钮就可以开始啦w')


def process_audio(message: Message):
    # Only when replying to voice or audio
    audio = message.audio or message.voice
    if not audio:
        return

    # Download audio file
    date = datetime.now().strftime('%Y-%m-%d %H-%M')
    try:
        downloader = bot.getFile(audio.file_id)
    except:
        downloader = bot.getFile(audio.file_id)
    file = Path(tmpdir).joinpath(f'{date} {message.from_user.name[1:]}.mp3')
    print(downloader, '->', file)
    downloader.download(file)

    # Segment file
    result = segment(file)

    # Null case
    print(result)
    if len(result) == 0:
        bot.send_message(message.chat_id, '分析失败, 大概是音量太小或者时长太短吧, 再试试w')
        return

    # Draw results
    with draw_ml(str(file), result) as buf:
        f, m, o, pf = get_result_percentages(result)
        msg = f"分析结果: {f*100:.0f}% 🙋‍♀️ | {m*100:.0f}% 🙋‍♂️ | {o*100:.0f}% 🚫\n" \
              f"(结果仅供参考, 如果结果不是你想要的，那就是模型的问题，欢迎反馈)\n" \
              f"" \
              f"(因为这个模型基于法语数据, 和中文发音习惯有差异, 所以这个识别结果可能不准)"
        bot.send_photo(message.chat_id, photo=buf, caption=msg,
                       reply_to_message_id=message.message_id)


def cmd_executor(u: Update, c: CallbackContext):
    reply = u.effective_message.reply_to_message

    # Parse command
    text = u.effective_message.text
    if not text:
        return
    cmd = text.lower().split()[0].strip()

    if cmd[0] not in '!/':
        return
    cmd = cmd[1:]

    if cmd not in ['analyze', 'ml', 'formant', 'pitch', 'stats']:
        return

    if u.effective_user.id == reply.from_user.id:
        process_audio(reply)
    else:
        r(u, '只有自己能分析自己的音频哦 👀')


def on_audio(u: Update, c: CallbackContext):
    process_audio(u.effective_message)


def get_result_percentages(result: list[ResultFrame]) -> tuple[float, float, float, float]:
    """
    Get percentages

    :param result: Result
    :return: %female, %male, %other, %female-vs-female+male
    """
    # Count total and categorical durations
    total_dur = 0
    durations: dict[str, int] = {f.label: 0 for f in result}
    for f in result:
        dur = f.end - f.start
        durations[f.label] += dur
        total_dur += dur

    # Convert durations to ratios
    for d in durations:
        durations[d] /= total_dur

    # Return results
    f = durations.get('female', 0)
    m = durations.get('male', 0)

    fm_total = f + m
    pf = 0 if fm_total == 0 else f / fm_total

    return f, m, 1 - f - m, pf


if __name__ == '__main__':
    utils.init_tf()

    warnings.filterwarnings("ignore")
    matplotlib.use('agg')

    seg = Segmenter()

    tmpdir = Path('audio_tmp')
    tmpdir.mkdir(exist_ok=True, parents=True)

    # Find telegram token
    path = Path(os.path.abspath(__file__)).parent
    db_path = path.joinpath('voice-bot-db.json')
    if 'tg_token' in os.environ:
        tg_token = os.environ['tg_token']
    else:
        with open(path.joinpath('voice-bot-token.txt'), 'r', encoding='utf-8') as f:
            tg_token = f.read().strip()

    # Telegram login
    updater = Updater(token=tg_token, use_context=True)
    dispatcher: Dispatcher = updater.dispatcher
    bot = updater.bot

    dispatcher.add_handler(CommandHandler('start', cmd_start, filters=Filters.chat_type.private))
    dispatcher.add_handler(CommandHandler('analyze', cmd_executor, filters=Filters.reply))
    dispatcher.add_handler(MessageHandler(Filters.reply, cmd_executor))
    dispatcher.add_handler(MessageHandler(Filters.voice & Filters.chat_type.private, on_audio))
    dispatcher.add_handler(MessageHandler(Filters.audio & Filters.chat_type.private, on_audio))

    print('Starting bot...')
    updater.start_polling()

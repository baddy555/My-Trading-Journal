from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import os

app = Flask(__name__)
# For Render hosting, we need a dynamic database path
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///trading_journal.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    exit_date = db.Column(db.Date)
    exit_price = db.Column(db.Float)
    quantity = db.Column(db.Integer, nullable=False)
    pnl = db.Column(db.Float)
    ai_analysis = db.Column(db.Text)
    my_notes = db.Column(db.Text)

@app.before_request
def create_tables():
    # This will create the database tables before the first request
    # in a production-ready way.
    db.create_all()

@app.route('/')
def dashboard():
    all_trades = Trade.query.order_by(Trade.entry_date.desc()).all()
    # (The rest of the dashboard stats calculation logic goes here...)
    closed_trades = [t for t in all_trades if t.pnl is not None]
    total_trades = len(closed_trades)
    winning_trades = len([t for t in closed_trades if t.pnl > 0])
    total_trades = len(closed_trades)
    winning_trades = len([t for t in closed_trades if t.pnl > 0])
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
    stats = {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2)
    }
    return render_template('dashboard.html', trades=all_trades, stats=stats)

@app.route('/add', methods=['POST'])
def add_new_trade():
    entry_date_str = request.form.get('entry_date')
    if not entry_date_str: return "Error: Entry date is required", 400
    new_trade = Trade(
        ticker=request.form.get('ticker'),
        entry_date=date.fromisoformat(entry_date_str),
        entry_price=float(request.form.get('entry_price')),
        quantity=int(request.form.get('quantity')),
        my_notes=request.form.get('my_notes')
    )
    db.session.add(new_trade)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/close/<int:trade_id>', methods=['POST'])
def close_trade(trade_id):
    trade_to_close = db.session.get(Trade, trade_id)
    if trade_to_close:
        exit_price = float(request.form.get('exit_price'))
        exit_date_str = request.form.get('exit_date')
        if not exit_date_str: return "Error: Exit date is required", 400
        trade_to_close.exit_date = date.fromisoformat(exit_date_str)
        trade_to_close.exit_price = exit_price
        profit = (exit_price - trade_to_close.entry_price) * trade_to_close.quantity
        trade_to_close.pnl = round(profit, 2)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:trade_id>')
def delete_trade(trade_id):
    trade_to_delete = db.session.get(Trade, trade_id)
    if trade_to_delete:
        db.session.delete(trade_to_delete)
        db.session.commit()
    return redirect(url_for('dashboard'))
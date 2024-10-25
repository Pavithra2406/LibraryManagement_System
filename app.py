from flask import Flask,render_template, redirect, url_for, session, flash, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Pavinithi%402406@localhost:3306/library_System'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)


LIBRARIAN_USERNAME = "admin"
LIBRARIAN_PASSWORD = "password123"

class Book(db.Model):
    __tablename__ = 'book'
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)

    transactions = relationship("Transaction", back_populates="book")


class Member(db.Model):
    __tablename__ = 'member'
    member_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    outstanding_debt = db.Column(db.Float, default=0.0)

    transactions = relationship("Transaction", back_populates="member")

class Transaction(db.Model):
    __tablename__ = 'transaction'
    transaction_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'))
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    date_returned = db.Column(db.DateTime, nullable=True)

    book = relationship("Book", back_populates="transactions")
    member = relationship("Member", back_populates="transactions")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == LIBRARIAN_USERNAME and password == LIBRARIAN_PASSWORD:
            session['logged_in'] = True
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/')
def home():
    if 'logged_in' in session:
        return render_template('home.html')
    return redirect(url_for('login'))


@app.route('/view_books', methods=['GET', 'POST'])
def view_books():

    search_query = request.form.get('search_query', '').strip()

    if search_query:

        books = Book.query.filter(
            (Book.title.ilike(f"%{search_query}%")) |
            (Book.author.ilike(f"%{search_query}%"))
        ).all()
    else:

        books = Book.query.all()

    return render_template('view_books.html', books=books, search_query=search_query)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']

        # Create new book entry
        new_book = Book(
            title=title,
            author=author,
        )
        db.session.add(new_book)
        db.session.commit()

        flash(f"'{title}' added successfully!", "success")
        return redirect(url_for('view_books'))

    return render_template('add_book.html')


@app.route('/book/<int:book_id>/<action>', methods=['GET', 'POST'])
def edit_or_delete_book(book_id, action):
    book = Book.query.get(book_id)

    if action == 'edit':
        if request.method == 'POST':
            book.title = request.form['title']
            book.author = request.form['author']
            db.session.commit()
            flash("Book details updated successfully!", "success")
            return redirect(url_for('view_books'))

        return render_template('edit_book.html', book=book)

    elif action == 'delete':
        db.session.delete(book)
        db.session.commit()
        flash("Book deleted successfully!", "success")
        return redirect(url_for('view_books'))

    flash("Invalid action specified.", "danger")
    return redirect(url_for('view_books'))


@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        address = request.form['address']
        new_member = Member(first_name=first_name, last_name=last_name, phone=phone, address=address)
        db.session.add(new_member)
        db.session.commit()
        return redirect(url_for('view_members'))
    return render_template('add_member.html')


@app.route('/view_members', methods=['GET', 'POST'])
def view_members():
    members = Member.query.all()

    if request.method == 'POST':
        # Handle payment
        if 'payment_amount' in request.form:
            member_id = request.form['member_id']
            payment_amount = float(request.form['payment_amount'])
            member = Member.query.get(member_id)
            if member:
                if payment_amount > 0:
                    member.outstanding_debt = max(0, member.outstanding_debt - payment_amount)
                    db.session.commit()
                    flash(
                        f"Payment of Rs. {payment_amount} received. Outstanding debt updated to Rs. {member.outstanding_debt}.",
                        "success")
                else:
                    flash("Payment amount must be greater than 0.", "warning")
            else:
                flash("Member not found.", "error")

        # Handle edit
        elif 'edit_member_id' in request.form:
            member_id = request.form['edit_member_id']
            member = Member.query.get(member_id)
            if member:
                member.first_name = request.form['first_name']
                member.last_name = request.form['last_name']
                member.phone = request.form['phone']
                member.address = request.form['address']
                db.session.commit()
                flash(f"Member {member.first_name} {member.last_name} updated successfully.", "success")
            else:
                flash("Member not found.", "error")

        # Handle delete
        elif 'delete_member_id' in request.form:
            member_id = request.form['delete_member_id']
            member = Member.query.get(member_id)
            if member:
                db.session.delete(member)
                db.session.commit()
                flash(f"Member {member.first_name} {member.last_name} deleted successfully.", "success")
            else:
                flash("Member not found.", "error")

    return render_template('view_members.html', members=members)

@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if request.method == 'POST':
        book_id = request.form['book_id']
        member_id = request.form['member_id']

        book = Book.query.get(book_id)
        member = Member.query.get(member_id)

        if book is None:
            flash("Book not found.", "error")
            return redirect(url_for('issue_book'))  # Use url_for for better practice

        if member is None:
            flash("Member not found.", "error")
            return redirect(url_for('issue_book'))


        transaction = Transaction(book_id=book_id, member_id=member_id, date_issued=datetime.now())
        db.session.add(transaction)
        db.session.commit()
        flash(f"Book ID {book_id} issued to Member ID {member_id}.", "success")
        return redirect(url_for('view_books'))


    return render_template('issue_book.html')


@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    rental_charge = None
    if request.method == 'POST':
        book_id = request.form['book_id']
        member_id = request.form['member_id']


        transaction = Transaction.query.filter_by(book_id=book_id, member_id=member_id, date_returned=None).first()

        if transaction:
            transaction.date_returned = datetime.now()

            days_issued = (transaction.date_returned - transaction.date_issued).days
            rental_charge = days_issued * 10  # Rs. 10 per day


            member = Member.query.get(member_id)
            if member.outstanding_debt + rental_charge <= 500:
                member.outstanding_debt += rental_charge
                db.session.commit()
                flash(f"Book returned. Rental charge: Rs. {rental_charge}. Outstanding debt updated to Rs. {member.outstanding_debt}.", "success")
            else:
                flash("Outstanding debt cannot exceed Rs. 500. Please settle your dues.", "warning")
                transaction.date_returned = None  # Rollback return
                db.session.commit()

            db.session.commit()
            return redirect('/view_books')
        else:
            flash("Invalid book or member ID, or book already returned.", "error")

    return render_template('return_book.html', rental_charge=rental_charge)



@app.route('/book_details', methods=['GET', 'POST'])
def book_details():
    book = None
    book_transactions = []

    if request.method == 'POST':
        book_id = request.form['book_id']  # Get the book ID from the form
        book = Book.query.get(book_id)  # Fetch the book using its ID


        book_transactions = Transaction.query.filter_by(book_id=book_id).all()

        if not book:  # Handle case where book does not exist
            return render_template('book_details.html', error="Book not found", book=None, book_transactions=[])

    return render_template('book_details.html', book=book, book_transactions=book_transactions)


@app.route('/member_transactions', methods=['GET', 'POST'])
def member_transactions():
    transactions = []
    member = None

    if request.method == 'POST':
        member_id = request.form['member_id']  # Get the member ID from the form


        member = Member.query.get(member_id)
        if member:
            transactions = Transaction.query.filter_by(member_id=member_id).all()
        else:
            flash("Member not found.", "error")

    return render_template('member_transactions.html', member=member, transactions=transactions)


@app.route('/transactions_by_date', methods=['GET', 'POST'])
def transactions_by_date():
    transactions = []
    if request.method == 'POST':
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']


        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')


                if start_date > end_date:
                    flash("End date must be after start date.", "error")
                    return render_template('transactions_by_date.html', transactions=None)


                transactions = Transaction.query.filter(
                    Transaction.date_issued >= start_date,
                    Transaction.date_issued <= end_date
                ).all()

                if not transactions:
                    flash("No transactions found for the selected date range.", "info")

            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "error")

    return render_template('transactions_by_date.html', transactions=transactions)



with app.app_context():
    db.create_all()
    print("Tables have been created successfully!")

if __name__ == '__main__':
    app.run(debug=True)

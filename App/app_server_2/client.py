import tkinter as tk
from tkinter import messagebox
import requests, time, threading
from server import server_ip


# login
def login():
    username = entry_username.get()
    password = entry_password.get()

    base_url = f'http://{server_ip}:5002/api/login'
    response = requests.post(
        base_url, json={'username': username, 'password': password})

    if response.status_code == 200:
        user_data = response.json()
        print("Login successful:", user_data)
        show_home_screen(username)
        return messagebox.showinfo('Login','Login successfully') 
    else:
        print("Error:", response.status_code, response.text)
        return messagebox.showerror('Login', 'Login failed')

# logout
def logout():
    username = current_user

    # Gọi API logout
    api_url = f"http://{server_ip}:5002/api/logout"
    response = requests.post(api_url, json={'username': username})

    if response.status_code == 200:
        print("Logout successful!", "success")
        show_login_screen()
        return messagebox.showinfo('Logout', 'Logout successed')
    else:
        print("Logout failed! User not found.")
        return messagebox.showerror('Logout', 'Logout failed')

# Transfer
def transfer():
    _from = current_user
    _to = entry_to_account.get()
    _amount = entry_amount.get()

    # Gọi API logout
    api_url = f"http://{server_ip}:5002/api/transfer"
    response = requests.post(api_url,json={'from_account': _from,'to_account': _to,'amount': _amount})

    if response.status_code == 200:
        get_balance()
        messagebox.showinfo("Transfer","Transfer successful!")
    else:
        get_balance()
        messagebox.showerror("Transfer","Transfer failed!")

# Lấy balance
def get_balance():
    try:
        # Gọi API để lấy số dư của user
        response = requests.get(f'http://{server_ip}:5002/api/user_balance/{current_user}')
        if response.status_code == 200:
            balance = response.json().get('balance')
            label_balance.config(text=f"Balance: {balance} USD")
        else:
            messagebox.showerror("Error", response.json().get('message'))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_balance_periodically():
    while True:
        try:
            get_balance()
            time.sleep(5)  # Kiểm tra lại mỗi 5 giây
        except Exception as e:
            print(f"Error updating balance: {str(e)}")
            break

# Hiển thị màn hình home
def show_home_screen(username):
    global current_user
    current_user = username
    login_frame.pack_forget()
    home_frame.pack()
    get_balance()

    # Hiển thị thông tin user
    label_welcome.config(text=f"Welcome {username}")

    threading.Thread(target=update_balance_periodically, daemon=True).start()


# # Hiển thị màn hình login
def show_login_screen():
    home_frame.pack_forget()
    login_frame.pack()

# Tạo giao diện chính
root = tk.Tk()
root.title("Banking App")

# Màn hình đăng nhập
login_frame = tk.Frame(root)
label_username = tk.Label(login_frame, text="Username:")
label_username.grid(row=0, column=0, padx=10, pady=10)
entry_username = tk.Entry(login_frame)
entry_username.grid(row=0, column=1, padx=10, pady=10)

label_password = tk.Label(login_frame, text="Password:")
label_password.grid(row=1, column=0, padx=10, pady=10)
entry_password = tk.Entry(login_frame, show="*")
entry_password.grid(row=1, column=1, padx=10, pady=10)

button_login = tk.Button(login_frame, text="Login", command=login)
button_login.grid(row=2, column=1, padx=10, pady=10)

# Màn hình home
home_frame = tk.Frame(root)
label_welcome = tk.Label(home_frame, text="Welcome")
label_welcome.grid(row=0, column=0, padx=10, pady=10)

label_balance = tk.Label(home_frame, text="Balance: 0 USD")
label_balance.grid(row=1, column=0, padx=10, pady=10)

label_to_account = tk.Label(home_frame, text="To Account:")
label_to_account.grid(row=2, column=0, padx=10, pady=10)
entry_to_account = tk.Entry(home_frame)
entry_to_account.grid(row=2, column=1, padx=10, pady=10)

label_amount = tk.Label(home_frame, text="Amount:")
label_amount.grid(row=3, column=0, padx=10, pady=10)
entry_amount = tk.Entry(home_frame)
entry_amount.grid(row=3, column=1, padx=10, pady=10)

button_transfer = tk.Button(home_frame, text="Transfer", command=transfer)
button_transfer.grid(row=4, column=1, padx=10, pady=10)

button_logout = tk.Button(home_frame, text="Logout", command=logout)
button_logout.grid(row=5, column=1, padx=10, pady=10)

# Bắt đầu với màn hình login
show_login_screen()

root.mainloop()

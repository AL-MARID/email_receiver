import requests
import time
import os
import sys
import json
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.box import ROUNDED
from rich.table import Table

console = Console()

class MailTM:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.email = None
        self.password = "SecurePass123!"
        self.monitoring = False
        self.last_raw_message = None
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        banner = """[cyan]
  ___ _ __ ___   __ _ _| |  _ __ ___  ___ ___ ___   _____ _ __ 
 / _ \ '_ ` _ \ / _` | | | | '__/ _ \/ __/ _ \ \ \ / / _ \ '__|
|  __/ | | | | | (_| | | | | | |  __/ (_|  __/ |\ V /  __/ |   
 \___|_| |_| |_|\__,_|_|_| |_|  \___|\___\___|_| \_/ \___|_|   
[/cyan]"""
        console.print(banner)
        console.print()
    
    def get_domain(self):
        response = requests.get(f"{self.base_url}/domains")
        domains = response.json()['hydra:member']
        return domains[0]['domain']
    
    def create_account(self, username=None):
        domain = self.get_domain()
        if not username:
            import random
            import string
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        
        self.email = f"{username}@{domain}"
        
        account_data = {
            "address": self.email,
            "password": self.password
        }
        
        response = requests.post(f"{self.base_url}/accounts", json=account_data)
        
        if response.status_code == 201:
            self.login()
            return True
        return False
    
    def login(self):
        login_data = {
            "address": self.email,
            "password": self.password
        }
        
        response = requests.post(f"{self.base_url}/token", json=login_data)
        
        if response.status_code == 200:
            self.token = response.json()['token']
            return True
        return False
    
    def get_messages(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/messages", headers=headers)
        
        if response.status_code == 200:
            return response.json()['hydra:member']
        return []
    
    def get_message_content(self, message_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/messages/{message_id}", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def display_account_created(self):
        tree = Tree("[bold green]Account Created[/bold green]")
        tree.add(f"[yellow]Email:[/yellow] [white]{self.email}[/white]")
        console.print(tree)
        console.print()
    
    def display_menu(self):
        table = Table(show_header=False, box=ROUNDED, border_style="cyan")
        table.add_row("[cyan]1[/cyan]", "[white]Change Email Name[/white]")
        table.add_row("[cyan]2[/cyan]", "[white]Generate New Random Email[/white]")
        table.add_row("[cyan]3[/cyan]", "[white]Start Monitoring Inbox[/white]")
        table.add_row("[cyan]0[/cyan]", "[white]Exit[/white]")
        console.print(table)
        console.print()
    
    def display_message(self, msg_data):
        from_info = f"{msg_data['from']['name']} <{msg_data['from']['address']}>"
        
        self.last_raw_message = msg_data
        
        content_panel = Panel(
            f"[yellow]From:[/yellow] [white]{from_info}[/white]\n"
            f"[yellow]Subject:[/yellow] [white]{msg_data['subject']}[/white]\n"
            f"[yellow]Date:[/yellow] [white]{msg_data['createdAt']}[/white]\n\n"
            f"[green]Content:[/green]\n[white]{msg_data.get('text', msg_data.get('html', 'No content'))}[/white]",
            title="[bold cyan]New Message Received[/bold cyan]",
            border_style="cyan",
            box=ROUNDED
        )
        console.print(content_panel)
        console.print()
        
        raw_content = ""
        raw_content += f"MESSAGE ID: {msg_data.get('id', 'N/A')}\n"
        raw_content += f"FROM: {msg_data.get('from', {})}\n"
        raw_content += f"TO: {msg_data.get('to', [])}\n"
        raw_content += f"CC: {msg_data.get('cc', [])}\n"
        raw_content += f"BCC: {msg_data.get('bcc', [])}\n"
        raw_content += f"SUBJECT: {msg_data.get('subject', 'N/A')}\n"
        raw_content += f"INTRO: {msg_data.get('intro', 'N/A')}\n"
        raw_content += f"SEEN: {msg_data.get('seen', False)}\n"
        raw_content += f"FLAGGED: {msg_data.get('flagged', False)}\n"
        raw_content += f"IS DELETED: {msg_data.get('isDeleted', False)}\n"
        raw_content += f"VERIFICATIONS: {msg_data.get('verifications', [])}\n"
        raw_content += f"RETENTION: {msg_data.get('retention', False)}\n"
        raw_content += f"RETENTION DATE: {msg_data.get('retentionDate', 'N/A')}\n"
        raw_content += f"HAS ATTACHMENTS: {msg_data.get('hasAttachments', False)}\n"
        raw_content += f"SIZE: {msg_data.get('size', 0)} bytes\n"
        raw_content += f"DOWNLOAD URL: {msg_data.get('downloadUrl', 'N/A')}\n"
        raw_content += f"CREATED AT: {msg_data.get('createdAt', 'N/A')}\n"
        raw_content += f"UPDATED AT: {msg_data.get('updatedAt', 'N/A')}\n"
        raw_content += "\n--- TEXT CONTENT ---\n"
        raw_content += f"{msg_data.get('text', 'No text content')}\n"
        raw_content += "\n--- HTML SOURCE CODE ---\n"
        raw_content += f"{msg_data.get('html', 'No HTML content')}\n"
        raw_content += "\n--- FULL JSON DUMP ---\n"
        raw_content += json.dumps(msg_data, indent=2, ensure_ascii=False)
        
        raw_panel = Panel(
            f"[white]{raw_content}[/white]",
            title="[bold yellow]Raw Message Data[/bold yellow]",
            border_style="yellow",
            box=ROUNDED
        )
        console.print(raw_panel)
        console.print()
    
    def monitor_inbox(self):
        self.monitoring = True
        seen_messages = set()
        
        self.clear_screen()
        self.show_banner()
        
        tree = Tree("[bold green]Monitoring Inbox[/bold green]")
        tree.add(f"[yellow]Email:[/yellow] [white]{self.email}[/white]")
        tree.add(f"[yellow]Status:[/yellow] [green]Active[/green]")
        tree.add(f"[yellow]Control:[/yellow] [white]Press Ctrl+C to pause and show menu[/white]")
        console.print(tree)
        console.print()
        
        while self.monitoring:
            try:
                messages = self.get_messages()
                
                for msg in messages:
                    if msg['id'] not in seen_messages:
                        seen_messages.add(msg['id'])
                        msg_content = self.get_message_content(msg['id'])
                        if msg_content:
                            self.display_message(msg_content)
                
                time.sleep(3)
            except KeyboardInterrupt:
                self.monitoring = False
                console.print("\n")
                
                if self.last_raw_message:
                    save_choice = console.input("[cyan]Save last raw message to file? (y/n):[/cyan] ")
                    console.print()
                    
                    if save_choice.lower() == 'y':
                        filename = f"message_{int(time.time())}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(self.last_raw_message, f, indent=2, ensure_ascii=False)
                        
                        tree = Tree("[bold green]Message Saved[/bold green]")
                        tree.add(f"[yellow]File:[/yellow] [white]{filename}[/white]")
                        console.print(tree)
                        console.print()
                
                tree = Tree("[bold yellow]Monitoring Paused[/bold yellow]")
                tree.add("[white]Returning to menu...[/white]")
                console.print(tree)
                console.print()
                time.sleep(1)
                break
    
    def show_menu(self):
        self.clear_screen()
        self.show_banner()
        
        tree = Tree("[bold cyan]Current Email[/bold cyan]")
        tree.add(f"[yellow]{self.email}[/yellow]")
        console.print(tree)
        console.print()
        
        while True:
            try:
                self.display_menu()
                choice = console.input("[cyan]Select option:[/cyan] ")
                console.print()
                
                if choice == "1":
                    new_name = console.input("[cyan]Enter new email name:[/cyan] ")
                    console.print()
                    self.clear_screen()
                    self.show_banner()
                    if self.create_account(new_name):
                        self.display_account_created()
                    else:
                        tree = Tree("[bold red]Error[/bold red]")
                        tree.add("[red]Failed to create account[/red]")
                        console.print(tree)
                        console.print()
                
                elif choice == "2":
                    self.clear_screen()
                    self.show_banner()
                    if self.create_account():
                        self.display_account_created()
                    else:
                        tree = Tree("[bold red]Error[/bold red]")
                        tree.add("[red]Failed to create account[/red]")
                        console.print(tree)
                        console.print()
                
                elif choice == "3":
                    self.monitor_inbox()
                
                elif choice == "0":
                    self.clear_screen()
                    self.show_banner()
                    tree = Tree("[bold green]Goodbye[/bold green]")
                    tree.add("[white]Thank you for using Email Receiver[/white]")
                    console.print(tree)
                    console.print()
                    sys.exit(0)
                
                else:
                    tree = Tree("[bold red]Invalid Option[/bold red]")
                    tree.add("[red]Please select a valid option[/red]")
                    console.print(tree)
                    console.print()
            except KeyboardInterrupt:
                console.print("\n")
                tree = Tree("[bold yellow]Notice[/bold yellow]")
                tree.add("[white]Use option 0 to exit[/white]")
                console.print(tree)
                console.print()
                continue
    
    def run(self):
        self.clear_screen()
        self.show_banner()
        
        tree = Tree("[bold cyan]Initializing[/bold cyan]")
        tree.add("[yellow]Creating new email account...[/yellow]")
        console.print(tree)
        console.print()
        
        if self.create_account():
            self.display_account_created()
            time.sleep(1)
            self.monitor_inbox()
            self.show_menu()
        else:
            tree = Tree("[bold red]Error[/bold red]")
            tree.add("[red]Failed to initialize[/red]")
            console.print(tree)
            console.print()

if __name__ == "__main__":
    mail = MailTM()
    mail.run()

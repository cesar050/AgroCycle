import { Component, HostListener, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})
export class NavbarComponent {
  scrolled = signal(false);
  menuAbierto = signal(false);
  darkMode = signal(false);

  @HostListener('window:scroll')
  onScroll() {
    this.scrolled.set(window.scrollY > 50);
  }

  toggleMenu() {
    this.menuAbierto.update(v => !v);
  }

  toggleDarkMode() {
    this.darkMode.update(v => !v);
    document.body.classList.toggle('dark-mode');
  }
}
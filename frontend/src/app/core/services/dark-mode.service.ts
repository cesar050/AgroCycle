import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class DarkModeService {
  darkMode = signal(false);

  toggleDark(): void {
    this.darkMode.update(v => !v);
    document.body.classList.toggle('dark');
  }
}

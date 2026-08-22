import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly BASE = environment.apiUrl;

  constructor(private http: HttpClient) {}

  get<T>(path: string, params?: any): Observable<T> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(k => {
        if (params[k] !== null && params[k] !== undefined) {
          httpParams = httpParams.set(k, params[k]);
        }
      });
    }
    return this.http.get<T>(`${this.BASE}${path}`, { params: httpParams });
  }

  post<T>(path: string, body: any): Observable<T> {
    return this.http.post<T>(`${this.BASE}${path}`, body);
  }

  put<T>(path: string, body: any): Observable<T> {
    return this.http.put<T>(`${this.BASE}${path}`, body);
  }

  patch<T>(path: string, body: any): Observable<T> {
    return this.http.patch<T>(`${this.BASE}${path}`, body);
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(`${this.BASE}${path}`);
  }
}
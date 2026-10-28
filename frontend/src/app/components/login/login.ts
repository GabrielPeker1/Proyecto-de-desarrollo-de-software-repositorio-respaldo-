import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {
  email = '';
  password = '';
  ingresando = false;
  error = '';

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private toastr: ToastrService,
    private changeDetector: ChangeDetectorRef
  ) {}

  login(): void {
    if (this.ingresando) {
      return;
    }
    this.ingresando = true;
    this.error = '';
    this.authService.login(this.email.trim(), this.password).subscribe({
      next: () => {
        this.toastr.success('Sesión iniciada.');
        if (this.authService.esModerador()) {
          this.router.navigateByUrl('/moderacion');
          return;
        }
        const requestedUrl = this.route.snapshot.queryParamMap.get('returnUrl');
        const destination = requestedUrl?.startsWith('/') && !requestedUrl.startsWith('//')
          ? requestedUrl
          : '/publicaciones';
        this.router.navigateByUrl(destination);
      },
      error: error => {
        console.error('No se pudo iniciar sesión.', error);
        const message = error?.error?.data;
        this.error = typeof message === 'string' ? message : 'No se pudo iniciar sesión. Revisá tus datos y que el servidor esté activo.';
        if (error?.status === 404) {
          this.toastr.warning(this.error, 'La cuenta no existe');
        } else {
          this.toastr.error(this.error);
        }
        this.ingresando = false;
        // Sin esto el botón se queda en "Ingresando..." hasta que se toque algo.
        this.changeDetector.detectChanges();
      }
    });
  }
}

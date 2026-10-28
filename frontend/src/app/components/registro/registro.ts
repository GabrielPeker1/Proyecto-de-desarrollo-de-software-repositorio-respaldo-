import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth';
import { UsuarioService } from '../../services/usuario';
import { SelectorUbicacion, UbicacionService } from '../../services/ubicacion';
import { PROVINCIAS_ARGENTINAS } from '../../data/provincias';

interface TipoUsuarioOption {
  id_tipo_usuario: number;
  nombre: string;
}

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  selector: 'app-registro',
  templateUrl: './registro.html',
  styleUrl: './registro.css',
})
export class Registro implements OnInit {
  readonly provincias = PROVINCIAS_ARGENTINAS;
  nombre = '';
  email = '';
  telefono = '';
  descripcion = '';
  ubicacion: SelectorUbicacion;
  calle = '';
  numero = '';
  piso = '';
  fotoPerfil = '';
  password = '';
  confirmarPassword = '';
  tipoUsuarioId: number | null = null;
  roles: TipoUsuarioOption[] = [];
  cargandoRoles = true;
  registrando = false;
  error = '';

  constructor(
    private http: HttpClient,
    private usuarios: UsuarioService,
    private ubicaciones: UbicacionService,
    private auth: AuthService,
    private router: Router,
    private toastr: ToastrService,
    private changeDetector: ChangeDetectorRef
  ) {
    this.ubicacion = new SelectorUbicacion(this.ubicaciones, () => this.changeDetector.detectChanges());
  }

  ngOnInit(): void {
    this.http.get<any>('/api/tipos-usuario/').subscribe({
      next: response => {
        const allRoles: TipoUsuarioOption[] = Array.isArray(response?.data) ? response.data : [];
        this.roles = allRoles.filter(role =>
          ['adoptante', 'rescatista'].includes(role.nombre.toLocaleLowerCase())
        );
        this.tipoUsuarioId = this.roles.find(role => role.nombre.toLocaleLowerCase() === 'rescatista')?.id_tipo_usuario
          ?? this.roles[0]?.id_tipo_usuario
          ?? null;
        this.cargandoRoles = false;
        if (this.roles.length === 0) {
          this.error = 'No se encontraron los tipos de cuenta. Verificá que el servidor tenga cargados los roles.';
        }
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudieron cargar los tipos de cuenta.', error);
        this.error = 'No se pudieron cargar los tipos de cuenta. Verificá que el servidor esté activo.';
        this.cargandoRoles = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  get contrasenasCoinciden(): boolean {
    return this.password === this.confirmarPassword;
  }

  seleccionarFoto(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    if (!file.type.startsWith('image/')) {
      this.toastr.warning('Seleccioná un archivo de imagen.');
      input.value = '';
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      this.toastr.warning('La imagen no puede superar los 2 MB.');
      input.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        this.fotoPerfil = reader.result;
      }
    };
    reader.onerror = () => {
      this.toastr.error('No se pudo leer la imagen seleccionada.');
      input.value = '';
    };
    reader.readAsDataURL(file);
    input.value = '';
  }

  get numeroValido(): boolean {
    return /^\d{1,6}$/.test(this.numero.trim());
  }

  registrar(): void {
    if (this.registrando || !this.tipoUsuarioId || !this.contrasenasCoinciden || !this.ubicacion.completa) {
      return;
    }
    this.registrando = true;
    this.error = '';

    this.ubicaciones.create({
      provincia: this.ubicacion.provincia,
      departamento: this.ubicacion.departamento,
      ciudad: this.ubicacion.ciudad,
      // La dirección completa la arma el back con estas tres partes.
      calle: this.calle.trim(),
      numero: this.numero.trim(),
      piso: this.piso.trim() || undefined,
      zona_aproximada: this.ubicacion.ciudad
    }).subscribe({
      next: locationResponse => {
        const locationId = locationResponse?.data?.id_ubicacion;
        if (!locationId) {
          this.error = 'El servidor no devolvió el identificador de la ubicación.';
          this.registrando = false;
          return;
        }
        this.crearUsuario(locationId);
      },
      error: error => {
        console.error('No se pudo guardar la ubicación del usuario.', error);
        this.error = this.errorMessage(error);
        this.registrando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  private crearUsuario(locationId: number): void {
    this.usuarios.create({
      nombre_completo: this.nombre.trim(),
      email: this.email.trim(),
      telefono: this.telefono.trim() || undefined,
      descripcion: this.descripcion.trim() || undefined,
      ubicacion_id: locationId,
      tipo_usuario_id: this.tipoUsuarioId!,
      password: this.password
    }).subscribe({
      next: response => {
        const userId = response?.data?.id_usuario;
        if (!userId) {
          this.error = 'La cuenta se creó sin devolver un identificador. Iniciá sesión manualmente.';
          this.registrando = false;
          return;
        }
        this.guardarFotoPerfil(userId);
        this.auth.login(this.email.trim(), this.password).subscribe({
          next: () => {
            this.toastr.success('Cuenta creada. ¡Bienvenido/a!');
            this.router.navigate(['/publicar']);
          },
          error: error => {
            console.error('La cuenta se creó, pero no se pudo iniciar la sesión automáticamente.', error);
            this.registrando = false;
            this.toastr.success('Cuenta creada. Iniciá sesión con tu correo y contraseña.');
            this.router.navigate(['/login']);
          }
        });
      },
      error: error => {
        console.error('No se pudo crear la cuenta.', error);
        if (error?.status === 409) {
          this.toastr.warning(this.errorMessage(error), 'El usuario ya existe');
        } else {
          this.toastr.error(this.errorMessage(error));
        }
        this.ubicaciones.delete(locationId).subscribe({
          next: () => {
            this.error = this.errorMessage(error);
            this.registrando = false;
            this.changeDetector.detectChanges();
          },
          error: cleanupError => {
            console.error('No se pudo quitar la ubicación creada tras fallar el registro.', cleanupError);
            this.error = `${this.errorMessage(error)} La ubicación quedó guardada; contactá al equipo si necesitás limpiarla.`;
            this.registrando = false;
            this.changeDetector.detectChanges();
          }
        });
      }
    });
  }

  private guardarFotoPerfil(userId: number): void {
    if (!this.fotoPerfil) {
      return;
    }
    try {
      localStorage.setItem(`perfil-foto-${userId}`, this.fotoPerfil);
    } catch (error) {
      console.error('No se pudo guardar la foto de perfil en este navegador.', error);
      this.toastr.warning('La cuenta se creó, pero no se pudo guardar la foto en este navegador.');
    }
  }

  private errorMessage(error: any): string {
    const data = error?.error?.data;
    if (typeof data === 'string') {
      return data;
    }
    if (data && typeof data === 'object') {
      return Object.values(data).flat().join(' ') || 'No se pudo crear la cuenta.';
    }
    return 'No se pudo completar el registro. Revisá la conexión con el servidor.';
  }
}

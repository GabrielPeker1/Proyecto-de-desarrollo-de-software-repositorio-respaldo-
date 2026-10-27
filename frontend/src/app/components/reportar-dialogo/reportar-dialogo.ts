import { ChangeDetectorRef, Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { CATEGORIAS_REPORTE, ReporteService } from '../../services/reporte';

/**
 * Ventana para reportar a un usuario o una publicación. La usan el chat y el
 * detalle de la publicación:
 *   <app-reportar-dialogo [idUsuario]="..." [nombre]="..." (cerrado)="..."></app-reportar-dialogo>
 * Con [idPublicacion] el reporte queda asociado a esa publicación.
 */
@Component({
  selector: 'app-reportar-dialogo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reportar-dialogo.html',
  styleUrl: './reportar-dialogo.css'
})
export class ReportarDialogo {
  @Input({ required: true }) idUsuario!: number;
  @Input() nombre = '';
  @Input() idPublicacion: number | null = null;
  @Input() titulo = '';
  @Input() aviso = 'El moderador va a poder ver la conversación entre ustedes.';
  @Output() cerrado = new EventEmitter<void>();

  readonly categorias = CATEGORIAS_REPORTE;
  categoria = '';
  motivo = '';
  enviando = false;

  constructor(
    private reportes: ReporteService,
    private toastr: ToastrService,
    private changeDetector: ChangeDetectorRef
  ) {}

  cerrar(): void {
    if (!this.enviando) {
      this.cerrado.emit();
    }
  }

  enviar(): void {
    const motivo = this.motivo.trim();
    if (!this.categoria || !motivo || this.enviando) {
      return;
    }
    this.enviando = true;
    this.reportes.reportar(this.idUsuario, this.categoria, motivo, this.idPublicacion).subscribe({
      next: () => {
        this.toastr.success('Reporte enviado. Un moderador lo va a revisar.');
        this.enviando = false;
        this.cerrado.emit();
      },
      error: error => {
        console.error('No se pudo enviar el reporte.', error);
        const data = error?.error?.data;
        this.toastr.error(typeof data === 'string' ? data : 'No se pudo enviar el reporte.');
        this.enviando = false;
        this.changeDetector.detectChanges();
      }
    });
  }
}

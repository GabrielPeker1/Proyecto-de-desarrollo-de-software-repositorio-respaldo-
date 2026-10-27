import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { ReporteService } from './reporte';

describe('ReporteService', () => {
  let service: ReporteService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient()] });
    service = TestBed.inject(ReporteService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

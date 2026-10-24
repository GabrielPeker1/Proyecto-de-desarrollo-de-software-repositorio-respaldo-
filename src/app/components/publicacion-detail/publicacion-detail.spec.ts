import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PublicacionDetail } from './publicacion-detail';

describe('PublicacionDetail', () => {
  let component: PublicacionDetail;
  let fixture: ComponentFixture<PublicacionDetail>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PublicacionDetail],
    }).compileComponents();

    fixture = TestBed.createComponent(PublicacionDetail);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

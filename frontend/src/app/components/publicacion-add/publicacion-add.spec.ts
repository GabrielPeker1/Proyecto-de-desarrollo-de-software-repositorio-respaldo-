import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PublicacionAdd } from './publicacion-add';

describe('PublicacionAdd', () => {
  let component: PublicacionAdd;
  let fixture: ComponentFixture<PublicacionAdd>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PublicacionAdd],
    }).compileComponents();

    fixture = TestBed.createComponent(PublicacionAdd);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

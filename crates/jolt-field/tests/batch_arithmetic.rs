#![cfg(feature = "solinas")]

use jolt_field::{Ext2, ExtField, Field, MulBaseUnreduced, One, Prime128Offset275, Ring, Zero};

type F = Prime128Offset275;
type E = Ext2<F>;

#[test]
fn batch_field_arithmetic_has_field_identities() {
    let values = [F::from_u64(2), -F::one(), F::from_u64(3)];
    assert_eq!(F::dot_product(&values, &values), F::from_u64(14));
    assert_eq!(F::dot_product(&values, &[F::from_u64(5)]), F::from_u64(10));
    assert_eq!(F::dot_product(&[], &values), F::zero());
    assert_eq!(
        F::signed_sum(values.iter().zip([false, true, true])),
        F::zero()
    );
    assert_eq!(F::signed_sum([]), F::zero());
    assert_eq!(F::sum_of_products::<0>(&[[], []]), F::from_u64(2));
    assert_eq!(F::sum_of_products::<4>(&[]), F::zero());
    assert_eq!(
        F::sum_of_products(&[[F::from_u64(2), -F::one(), F::from_u64(3)]]),
        -F::from_u64(6)
    );
}

#[test]
fn extension_row_dots_respect_the_canonical_basis() {
    let powers = [
        E::from_base_slice(&[F::from_u64(2), F::from_u64(3)]),
        E::one(),
    ];
    let row = [F::from_u64(5), -F::one()];
    let rows = [&row[..], &[][..]];
    let expected = E::from_base_slice(&[F::from_u64(9), F::from_u64(15)]);
    assert_eq!(E::dot_base(&powers, &row), expected);
    let mut output = [E::zero()];
    E::dot_base_rows(&powers, &rows[..1], &mut output);
    assert_eq!(output, [expected]);
    assert_eq!(
        E::weighted_dot_base_rows(&rows[..1], &[-E::one()], &powers),
        -expected
    );
    E::dot_base_rows(&[], &rows[1..], &mut output);
    assert_eq!(output, [E::zero()]);
    assert_eq!(E::weighted_dot_base_rows(&[], &[], &powers), E::zero());
}

#[test]
#[should_panic(expected = "assertion")]
fn row_dots_reject_truncated_rows() {
    E::dot_base_rows(&[E::one()], &[&[]], &mut [E::zero()]);
}

#[test]
#[should_panic(expected = "assertion")]
fn weighted_row_dots_reject_missing_weights() {
    let _ = E::weighted_dot_base_rows(&[&[]], &[], &[]);
}
